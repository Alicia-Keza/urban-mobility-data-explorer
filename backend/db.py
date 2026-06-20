import mysql.connector.pooling

from backend.config import Config

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="um_pool",
    pool_size=8,
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME,
)

def query_all(sql, params=None):
    # Run a SELECT and give back every row as a dict, like {"trips": 100}.
    connection = pool.get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        # Always hand the connection back to the pool, even if the query failed.
        connection.close()

def query_one(sql, params=None):
    # Same as query_all but for queries that should return just one row.
    rows = query_all(sql, params)
    return rows[0] if rows else None
