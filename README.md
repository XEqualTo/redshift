# Amazon Redshift - In-Depth Learning

## **Understanding Amazon Redshift**

### **1. What is Redshift?**
Amazon Redshift is a **fully managed, petabyte-scale data warehouse service** designed for **OLAP (Online Analytical Processing)** workloads. It allows businesses to run complex analytical queries efficiently on large datasets.

### **2. How Does Redshift Work?**
- **Columnar Storage:** Unlike traditional row-based databases, Redshift stores data in **columns**, which makes it extremely fast for analytical queries.
- **Massively Parallel Processing (MPP):** Redshift distributes query execution across multiple nodes for speed.
- **Compression:** Data is stored in a compressed format by default, reducing storage costs and improving performance.
- **Zone Maps:** Redshift keeps track of min/max values of each data block to quickly eliminate unnecessary scans.

### **3. Redshift System Design**
- **Leader Node:** Manages query execution and distributes tasks to Compute Nodes.
- **Compute Nodes:** Store data and execute queries in parallel.
- **Columnar Storage:** Optimized for analytics, reducing I/O costs.
- **Distribution Styles:** Determines how data is spread across nodes.
- **Sort Keys:** Help optimize query performance by pre-sorting data.

---

## **Performance Tuning in Amazon Redshift**

### 🔹 **1. Check Table Storage Usage**  
Before optimizing, check **how much space your tables use**.  

```sql
SELECT "table", size AS mb 
FROM svv_table_info 
ORDER BY size DESC 
LIMIT 10;
```
✅ This shows the **biggest tables**, so you can **optimize the largest ones first**.  

---

### 🔹 **2. Check Column-Level Compression**  
Redshift **compresses data by default**, but let's verify:  

```sql
SELECT "column", encoding, pct_used 
FROM svv_columns 
WHERE table_name = 'orders';
```
✅ **Good compression → High `pct_used`**  
❌ **No compression (`NONE` encoding) → Wastes storage**  

---

### 🔹 **3. Apply Compression (If Needed)**  
If a column **is not compressed**, manually apply the best **encoding**.  
- Use **LZO** for strings  
- Use **ZSTD** for integers & floats (better compression)  

```sql
CREATE TABLE orders_compressed 
(
    order_id INT ENCODE ZSTD, 
    customer_id INT ENCODE ZSTD, 
    order_date DATE ENCODE LZO, 
    amount DECIMAL(10,2) ENCODE ZSTD
) 
BACKUP NO;
```
✅ `BACKUP NO` avoids **unnecessary backups** for temp tables.  

---

### 🔹 **4. Automatically Apply Compression**  
If you're loading new data, **let Redshift auto-compress**:  

```sql
COPY orders FROM 's3://your-bucket/orders.csv' 
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftRole' 
FORMAT AS CSV 
COMPUPDATE ON;
```
✅ `COMPUPDATE ON` **automatically chooses the best encoding**.  

---

## **Data Distribution & Skew Handling**

### 🔹 **Checking Row Distribution**
To ensure even distribution across nodes, check row count per slice:

```sql
SELECT slice, COUNT(*) AS row_count
FROM stv_blocklist
GROUP BY slice;
```
✅ If row counts are **uneven**, the table is **skewed**, which can cause slow queries.

### 🔹 **Fixing Skew with KEY Distribution**
If `customer_id` is commonly used in joins and has **high cardinality (many unique values)**, use it as the `DISTKEY`:

```sql
CREATE TABLE orders (
    order_id INT,
    customer_id INT DISTKEY,
    order_date DATE,
    amount DECIMAL(10,2)
)
SORTKEY(order_date);
```
✅ This ensures **even distribution** across nodes, improving join performance.

---

Would you like to move on to **query optimization techniques** next? 🚀

