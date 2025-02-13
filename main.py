import psycopg2
from typing import List, Dict

class RedshiftConnection:
    def __init__(self, host: str, dbname: str, user: str, password: str, port: int = 5439):
        self.connection = psycopg2.connect(
            host=host,
            dbname=dbname,
            user=user,
            password=password,
            port=port
        )
    
    def execute_query(self, query: str) -> List[Dict]:
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def close(self):
        self.connection.close()

class TableDistributionChecker:
    def __init__(self, connection: RedshiftConnection):
        self.connection = connection
    
    def get_skewed_tables(self) -> List[Dict]:
        query = """
        SELECT table, skew_rows, skew_sortkey1
        FROM svv_table_info
        WHERE skew_rows > 1.5 OR skew_sortkey1 > 1.5
        ORDER BY skew_rows DESC;
        """
        return self.connection.execute_query(query)

class SortKeyDistributionChecker:
    def __init__(self, connection: RedshiftConnection):
        self.connection = connection
    
    def get_unoptimized_sortkeys(self) -> List[Dict]:
        query = """
        SELECT table, unsorted
        FROM svv_table_info
        WHERE unsorted > 20
        ORDER BY unsorted DESC;
        """
        return self.connection.execute_query(query)

class TableBloatChecker:
    def __init__(self, connection: RedshiftConnection):
        self.connection = connection
    
    def get_bloated_tables(self) -> List[Dict]:
        query = """
        SELECT table, pct_used
        FROM svv_table_info
        WHERE pct_used < 70
        ORDER BY pct_used ASC;
        """
        return self.connection.execute_query(query)

class VacuumStatusChecker:
    def __init__(self, connection: RedshiftConnection):
        self.connection = connection
    
    def get_vacuum_status(self) -> List[Dict]:
        query = """
        SELECT table_id, status
        FROM stl_vacuum
        ORDER BY starttime DESC;
        """
        return self.connection.execute_query(query)

if __name__ == "__main__":
    conn = RedshiftConnection(host="your-redshift-host", dbname="your-db", user="your-user", password="your-password")
    
    distribution_checker = TableDistributionChecker(conn)
    sortkey_checker = SortKeyDistributionChecker(conn)
    bloat_checker = TableBloatChecker(conn)
    vacuum_checker = VacuumStatusChecker(conn)
    
    print("Skewed Tables:", distribution_checker.get_skewed_tables())
    print("Unoptimized Sort Keys:", sortkey_checker.get_unoptimized_sortkeys())
    print("Bloated Tables:", bloat_checker.get_bloated_tables())
    print("Vacuum Status:", vacuum_checker.get_vacuum_status())
    
    conn.close()
