import sqlite3
import pandas as pd
import os

def create_database():
    # Create database connection
    db_path = 'mosquito_net.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create survey table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS survey (
        hhid TEXT PRIMARY KEY,
        selected_district TEXT,
        selected_subcounty TEXT,
        selected_parish TEXT,
        selected_village TEXT,
        gpsloc TEXT
    )
    ''')

    # Create campaign nets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS campnets (
        net_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hhid TEXT,
        brand TEXT,
        distribution_date DATE,
        FOREIGN KEY (hhid) REFERENCES survey (hhid)
    )
    ''')

    # Create lost nets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lostnets (
        lost_net_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hhid TEXT,
        reason TEXT,
        loss_date DATE,
        FOREIGN KEY (hhid) REFERENCES survey (hhid)
    )
    ''')

    # Commit and close
    conn.commit()
    conn.close()

    print(f"Database created successfully at: {os.path.abspath(db_path)}")

def load_data():
    try:
        # Load CSV files
        survey_df = pd.read_csv('survey.csv')
        campnets_df = pd.read_csv('campnets.csv')
        lostnets_df = pd.read_csv('lostnets.csv')

        # Connect to database
        conn = sqlite3.connect('mosquito_net.db')

        # Insert data into tables
        survey_df.to_sql('survey', conn, if_exists='replace', index=False)
        campnets_df.to_sql('campnets', conn, if_exists='replace', index=False)
        lostnets_df.to_sql('lostnets', conn, if_exists='replace', index=False)

        print("Data loaded successfully into the database!")

    except FileNotFoundError as e:
        print(f"Error: Could not find one or more CSV files. {str(e)}")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
    load_data() 