import os
import logging
import asyncio
import aiopg
import csv
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RedshiftConnection:
    """Manages an asynchronous connection to Amazon Redshift and executes queries efficiently."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        """Initialize a connection pool."""
        self.pool = await aiopg.create_pool(self.dsn, minsize=1, maxsize=5)
        logging.info("Connected to Redshift (Async)")

    async def execute_query(self, query: str) -> List[Dict]:
        """Executes a SQL query asynchronously and returns the results."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                if cursor.rowcount == 0:
                    logging.warning(f"No results for query: {query}")
                    return []
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in await cursor.fetchall()]

    async def close(self):
        """Closes the connection pool."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logging.info("Closed Redshift connection pool")

class HealthCheck:
    """Executes Redshift health checks and saves results to CSV files asynchronously."""

    def __init__(self, connection: RedshiftConnection, output_dir: str):
        self.connection = connection
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def run_check(self, query: str, filename: str):
        """Runs a health check query and saves results asynchronously."""
        logging.info(f"Running query for {filename}...")
        results = await self.connection.execute_query(query)
        if results:
            await self.save_to_csv(results, filename)
        else:
            logging.warning(f"No data for {filename}, skipping CSV export.")

    async def save_to_csv(self, data: List[Dict], filename: str):
        """Asynchronously saves query results to a CSV file."""
        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        try:
            async with aiofiles.open(filepath, mode="w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                await file.write(",".join(data[0].keys()) + "\n")
                for row in data:
                    await file.write(",".join(str(value) for value in row.values()) + "\n")
            logging.info(f"Saved results to {filepath}")
        except Exception as e:
            logging.error(f"Failed to write CSV for {filename}: {e}")

async def main():
    """Main function to execute health checks asynchronously."""
    # Load credentials securely from environment variables
    host = os.getenv("REDSHIFT_HOST")
    dbname = os.getenv("REDSHIFT_DB")
    user = os.getenv("REDSHIFT_USER")
    password = os.getenv("REDSHIFT_PASSWORD")
    port = int(os.getenv("REDSHIFT_PORT", 5439))

    if not all([host, dbname, user, password]):
        logging.critical("Missing one or more required environment variables (REDSHIFT_HOST, REDSHIFT_DB, REDSHIFT_USER, REDSHIFT_PASSWORD).")
        return

    dsn = f"dbname={dbname} user={user} password={password} host={host} port={port}"
    conn = RedshiftConnection(dsn)

    await conn.connect()

    output_dir = f"pde-data-{dbname}-healthcheck"
    health_check = HealthCheck(conn, output_dir)

    queries = {
        "SkewedTables": "SELECT table, skew_rows FROM svv_table_info WHERE skew_rows > 1.5 ORDER BY skew_rows DESC;",
        "UnoptimizedSortKeys": "SELECT table, unsorted FROM svv_table_info WHERE unsorted > 20 ORDER BY unsorted DESC;",
        "BloatedTables": "SELECT table, pct_used FROM svv_table_info WHERE pct_used < 70 ORDER BY pct_used ASC;",
        "VacuumStatus": "SELECT table_id, status FROM stl_vacuum ORDER BY starttime DESC;"
    }

    await asyncio.gather(*(health_check.run_check(query, name) for name, query in queries.items()))

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
