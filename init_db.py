"""Database initialization: create tables and import seed data."""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mysql_qa.db.mysql_client import MysqlClient

client = MysqlClient()

# Step 1: Create jpkb table
print("Creating jpkb table...")
client.create_table()

# Step 2: Import seed CSV data
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "mysql_qa", "data", "TCM中药知识问答.csv")
print(f"Importing seed data from: {csv_path}")
client.insert_csv(csv_path)

# Step 3: Verify
questions = client.fetch_all_questions()
print(f"Done. jpkb table now has {len(questions)} questions.")

client.close()
