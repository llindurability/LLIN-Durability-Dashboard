import os
import pyodbc
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create and return a database connection"""
    conn_str = (
        f"DRIVER={os.getenv('DB_DRIVER')};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
    )
    
    @contextmanager
    def conn_context():
        conn = None
        try:
            conn = pyodbc.connect(conn_str, timeout=30)
            yield conn
        finally:
            if conn:
                conn.close()
    
    return conn_context()

def execute_query(query, params=None):
    """Execute a query and return results"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return results, columns
        else:
            conn.commit()
            
    finally:
        conn.close() 