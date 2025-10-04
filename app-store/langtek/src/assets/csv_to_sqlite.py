#!/usr/bin/env python3
import csv
import sqlite3
import os

# Input and output files
csv_file = 'es-en.csv'
db_file = 'es-en.sqlite3'

# Remove existing database if it exists
if os.path.exists(db_file):
    os.remove(db_file)

# Connect to SQLite database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create table with the same schema as es-en.sqlite3
cursor.execute('''
CREATE TABLE translations (
    spanish TEXT PRIMARY KEY,
    english TEXT
)
''')

# Create index on spanish column
cursor.execute('CREATE INDEX idx_spanish ON translations(spanish)')

# Read CSV file and insert data into database
with open(csv_file, 'r', encoding='utf-8') as f:
    csv_reader = csv.reader(f)
    next(csv_reader)  # Skip header row
    
    # Insert data
    for row in csv_reader:
        if len(row) >= 2:
            cursor.execute('INSERT OR IGNORE INTO translations (spanish, english) VALUES (?, ?)', 
                          (row[0], row[1]))

# Commit changes and close connection
conn.commit()
conn.close()

print(f"Conversion complete. Created {db_file} from {csv_file}")
