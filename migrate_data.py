import sqlite3
import pandas as pd
from database import get_db_connection

def migrate_data():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('your_old_database.db')
    
    # Read data from SQLite
    survey_df = pd.read_sql_query("SELECT * FROM survey", sqlite_conn)
    campnets_df = pd.read_sql_query("SELECT * FROM campnets", sqlite_conn)
    lostnets_df = pd.read_sql_query("SELECT * FROM lostnets", sqlite_conn)
    
    sqlite_conn.close()
    
    # Connect to SQL Server and insert data
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert survey data
        for _, row in survey_df.iterrows():
            cursor.execute("""
                INSERT INTO survey (hhid, selected_district, selected_subcounty, 
                                  selected_parish, selected_village, gpsloc)
                VALUES (?, ?, ?, ?, ?, ?)
            """, tuple(row))
            
        # Insert campnets data
        for _, row in campnets_df.iterrows():
            cursor.execute("""
                INSERT INTO campnets (hhid, brand, distribution_date)
                VALUES (?, ?, ?)
            """, tuple(row))
            
        # Insert lostnets data
        for _, row in lostnets_df.iterrows():
            cursor.execute("""
                INSERT INTO lostnets (hhid, reason, loss_date)
                VALUES (?, ?, ?)
            """, tuple(row))
        
        conn.commit()

if __name__ == "__main__":
    migrate_data() 