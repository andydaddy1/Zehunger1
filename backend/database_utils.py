import mysql.connector
from mysql.connector import Error
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if conn.is_connected():
            print(f"Successfully connected to database: {DB_NAME}")
            return conn
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def execute_query(query, params=None, fetch_one=False, fetch_all=False, is_insert=False):
    """Executes a given SQL query."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        
        cursor = conn.cursor(dictionary=True if not is_insert else False) # dictionary=True for SELECT to get col names
        cursor.execute(query, params)
        
        if is_insert:
            conn.commit()
            print(f"Insert successful. Last inserted ID: {cursor.lastrowid}")
            return cursor.lastrowid
        elif fetch_one:
            result = cursor.fetchone()
            return result
        elif fetch_all:
            result = cursor.fetchall()
            return result
        else: # For UPDATE, DELETE, or other non-SELECT/non-INSERT queries
            conn.commit()
            return cursor.rowcount # Number of rows affected
            
    except Error as e:
        print(f"Error executing query: {e}")
        if conn and is_insert: # Rollback in case of error during insert
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print(f"MySQL connection to {DB_NAME} is closed")

# Example usage (you can remove this or keep for testing)
if __name__ == '__main__':
    # Test connection
    connection = get_db_connection()
    if connection:
        connection.close()
        print("Test connection successful and closed.")
    
    # Example: Create a table (You should run this directly in MySQL or use a migration tool)
    # create_table_sql = """
    # CREATE TABLE IF NOT EXISTS test_table (
    #     id INT AUTO_INCREMENT PRIMARY KEY,
    #     name VARCHAR(255) NOT NULL,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # );
    # """
    # print("Attempting to create test_table...")
    # execute_query(create_table_sql)
    # print("Finished attempting to create test_table.")
    
    # Example: Insert data
    # insert_sql = "INSERT INTO test_table (name) VALUES (%s)"
    # last_id = execute_query(insert_sql, params=("Test Name",), is_insert=True)
    # if last_id:
    #     print(f"Inserted data with ID: {last_id}")
        
    # Example: Select data
    # select_sql = "SELECT * FROM test_table"
    # records = execute_query(select_sql, fetch_all=True)
    # if records:
    #     print("Records found:", records) 