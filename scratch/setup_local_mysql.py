import pymysql
import os

host = 'localhost'
port = 3306
user = 'root'
password = 'root'

print("[1] Connecting to local MySQL...")
conn = pymysql.connect(host=host, port=port, user=user, password=password, autocommit=True)
cursor = conn.cursor()

print("[2] Creating database carpooling_db...")
cursor.execute("CREATE DATABASE IF NOT EXISTS carpooling_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
cursor.execute("USE carpooling_db;")

sql_files = [
    'database/01_schema.sql',
    'database/02_triggers_procedures.sql',
    'database/03_seed_data.sql'
]

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for fpath in sql_files:
    full_path = os.path.join(base_dir, fpath)
    if os.path.exists(full_path):
        print(f"[3] Executing {fpath}...")
        with open(full_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Split commands by semicolon or delimiter
        commands = sql_content.split(';')
        for cmd in commands:
            cmd_clean = cmd.strip()
            if cmd_clean and not cmd_clean.startswith('--'):
                try:
                    cursor.execute(cmd_clean)
                except Exception as e:
                    print(f"   [WARN] Command warning/error: {e}")

cursor.execute("SHOW TABLES;")
tables = cursor.fetchall()
print("\n[SUCCESS] Local MySQL Database Initialized!")
print("Tables in carpooling_db:", [t[0] for t in tables])

conn.close()
