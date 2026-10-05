import pymysql

passwords = ['', 'root', 'password', '1234', 'admin', '123456', 'root123']
connected_pw = None

for pw in passwords:
    try:
        conn = pymysql.connect(host='localhost', port=3306, user='root', password=pw, connect_timeout=3)
        print(f"[SUCCESS] Connected to local MySQL with user='root', password='{pw}'")
        connected_pw = pw
        conn.close()
        break
    except Exception as e:
        print(f"[INFO] Tried password '{pw}': {e}")

if connected_pw is not None:
    print(f"\nROOT_PASSWORD={connected_pw}")
