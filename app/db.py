"""
Database Connection & Management Layer for CabShare DBMS Project
Includes Women-Only pools, 5-Star Ratings & Reviews, CO2 emissions savings,
and Weekly/Monthly Commute Passes with automatic seat assignment.
"""

import os
import sqlite3
import datetime
from decimal import Decimal
from contextlib import contextmanager

def _json_serialize_value(v):
    if isinstance(v, datetime.timedelta):
        total_seconds = int(v.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    elif isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
        return str(v)
    elif isinstance(v, Decimal):
        return float(v)
    return v

def _sanitize_row(row):
    if not row:
        return row
    return {k: _json_serialize_value(v) for k, v in dict(row).items()}

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

try:
    import mysql.connector
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    HAS_MYSQL_CONNECTOR = False

# Database Configuration
DB_ENGINE = os.getenv('DB_ENGINE', 'mysql').lower()
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'carpooling_db')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', 'https://baal-db05a-default-rtdb.asia-southeast1.firebasedatabase.app')

if os.getenv('VERCEL') or not os.access(os.path.dirname(__file__), os.W_OK):
    SQLITE_DB_PATH = '/tmp/carpooling_local.db'
else:
    SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'carpooling_local.db')

_active_engine = None

def sync_to_firebase(node_path, data):
    """Pushes live event data to Firebase Realtime Database for instant phone<->PC WebSockets sync."""
    try:
        import urllib.request
        import json
        url = f"{FIREBASE_DATABASE_URL.rstrip('/')}/{node_path.lstrip('/')}.json"
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='PATCH'
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            pass
    except Exception as e:
        print(f"[WARN] Firebase sync error: {e}")

def get_from_firebase(node_path):
    """Fetches cloud record from Firebase Realtime Database."""
    try:
        import urllib.request
        import json
        url = f"{FIREBASE_DATABASE_URL.rstrip('/')}/{node_path.lstrip('/')}.json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"[WARN] Firebase fetch error: {e}")
        return None

def get_active_engine():

    global _active_engine
    if _active_engine is not None:
        return _active_engine
    
    if DB_ENGINE == 'mysql' and (HAS_PYMYSQL or HAS_MYSQL_CONNECTOR):
        if HAS_PYMYSQL:
            try:
                ssl_opts = {'ssl': True} if DB_PORT != 3306 else None
                conn = pymysql.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    ssl=ssl_opts,
                    connect_timeout=3
                )
                conn.close()
                _active_engine = 'mysql'
                print("[INFO] Connected to MySQL database via PyMySQL successfully.")
                return _active_engine
            except Exception as e:
                print(f"[WARN] MySQL not reachable ({e}). Falling back to SQLite local database.")
                _active_engine = 'sqlite'
                _init_sqlite_db()
                return _active_engine
        elif HAS_MYSQL_CONNECTOR:
            try:
                conn = mysql.connector.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    connection_timeout=3
                )
                conn.close()
                _active_engine = 'mysql'
                print("[INFO] Connected to MySQL database via mysql-connector successfully.")
                return _active_engine
            except Exception as e:
                print(f"[WARN] MySQL not reachable ({e}). Falling back to SQLite local database.")
                _active_engine = 'sqlite'
                _init_sqlite_db()
                return _active_engine
    
    _active_engine = 'sqlite'
    _init_sqlite_db()
    return _active_engine

@contextmanager
def get_db():
    engine = get_active_engine()
    if engine == 'mysql':
        if HAS_PYMYSQL:
            ssl_opts = {'ssl': True} if DB_PORT != 3306 else None
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                ssl=ssl_opts,
                autocommit=True
            )
            try:
                yield conn
            finally:
                conn.close()
        elif HAS_MYSQL_CONNECTOR:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True
            )
            try:
                yield conn
            finally:
                conn.close()
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

def execute_query(sql, params=None, fetchone=False):
    """Executes a SELECT query and returns rows as list of dicts."""
    engine = get_active_engine()
    with get_db() as conn:
        cursor = conn.cursor()
        
        if engine == 'sqlite' and params:
            sql_adapted = sql.replace('%s', '?')
        else:
            sql_adapted = sql
            
        cursor.execute(sql_adapted, params or ())
        
        if fetchone:
            row = cursor.fetchone()
            if row is None:
                return None
            return _sanitize_row(row)
        else:
            rows = cursor.fetchall()
            return [_sanitize_row(r) for r in rows]

def execute_update(sql, params=None):
    """Executes an INSERT, UPDATE, or DELETE query and returns (lastrowid, rowcount)."""
    engine = get_active_engine()
    with get_db() as conn:
        cursor = conn.cursor()
        
        if engine == 'sqlite':
            sql_adapted = sql.replace('%s', '?') if params else sql
        else:
            sql_adapted = sql.replace('INSERT OR IGNORE INTO', 'INSERT IGNORE INTO').replace('INSERT OR REPLACE INTO', 'REPLACE INTO')
            
        cursor.execute(sql_adapted, params or ())
        
        if engine == 'sqlite':
            conn.commit()
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
        else:
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
            
        return last_id, row_count

def _init_sqlite_db(force_reinit=False):
    """Initializes SQLite database with all tables including passes and reviews."""
    if os.path.exists(SQLITE_DB_PATH) and not force_reinit:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT Pass_ID FROM COMMUTE_PASS LIMIT 1")
            conn.close()
            return
        except:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    schema_script = """
    DROP TABLE IF EXISTS COMMUTE_PASS;
    DROP TABLE IF EXISTS RATING_REVIEW;
    DROP TABLE IF EXISTS CHAT;
    DROP TABLE IF EXISTS NOTIFICATION;
    DROP TABLE IF EXISTS FRIEND;
    DROP TABLE IF EXISTS RIDE_REQUEST;
    DROP TABLE IF EXISTS STOP;
    DROP TABLE IF EXISTS RIDE;
    DROP TABLE IF EXISTS USER;

    CREATE TABLE IF NOT EXISTS USER (
        User_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Phone_Number TEXT NOT NULL UNIQUE,
        Password TEXT NOT NULL,
        Email TEXT DEFAULT NULL,
        Gender TEXT NOT NULL DEFAULT 'Other',
        Profile_Picture TEXT DEFAULT 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
        Total_Money_Saved REAL NOT NULL DEFAULT 0.00,
        Average_Rating REAL NOT NULL DEFAULT 5.00,
        Total_Reviews INTEGER NOT NULL DEFAULT 0,
        CO2_Saved_Kg REAL NOT NULL DEFAULT 0.00,
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS RIDE (
        Ride_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Driver_ID INTEGER NOT NULL,
        Source TEXT NOT NULL,
        Destination TEXT NOT NULL,
        Date DATE NOT NULL,
        Time TIME NOT NULL,
        Total_Seats INTEGER NOT NULL,
        Available_Seats INTEGER NOT NULL,
        Fare_Per_Seat REAL NOT NULL DEFAULT 0.00,
        Total_Cab_Fare REAL NOT NULL DEFAULT 0.00,
        Ride_Type TEXT NOT NULL DEFAULT 'Cab_Share',
        Vehicle_Info TEXT NOT NULL DEFAULT 'Uber / Ola Cab',
        Is_Women_Only BOOLEAN NOT NULL DEFAULT 0,
        Estimated_Distance_Km REAL NOT NULL DEFAULT 25.00,
        Ride_Status TEXT NOT NULL DEFAULT 'Scheduled',
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Driver_ID) REFERENCES USER(User_ID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS STOP (
        Stop_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Ride_ID INTEGER NOT NULL,
        Stop_Name TEXT NOT NULL,
        Stop_Order INTEGER NOT NULL,
        Arrival_Time TIME,
        Estimated_Sub_Fare REAL NOT NULL DEFAULT 0.00,
        Latitude REAL,
        Longitude REAL,
        FOREIGN KEY (Ride_ID) REFERENCES RIDE(Ride_ID) ON DELETE CASCADE,
        UNIQUE (Ride_ID, Stop_Order)
    );

    CREATE TABLE IF NOT EXISTS RIDE_REQUEST (
        Request_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        User_ID INTEGER NOT NULL,
        Ride_ID INTEGER NOT NULL,
        Pickup_Point TEXT,
        Dropoff_Point TEXT,
        Seats_Requested INTEGER NOT NULL DEFAULT 1,
        Agreed_Fare REAL NOT NULL DEFAULT 0.00,
        Request_Status TEXT NOT NULL DEFAULT 'Pending',
        Request_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (User_ID) REFERENCES USER(User_ID) ON DELETE CASCADE,
        FOREIGN KEY (Ride_ID) REFERENCES RIDE(Ride_ID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS CHAT (
        Chat_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Request_ID INTEGER DEFAULT NULL,
        Sender_ID INTEGER NOT NULL,
        Receiver_ID INTEGER NOT NULL,
        Message TEXT NOT NULL,
        Sent_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Seen_Status TEXT NOT NULL DEFAULT 'Unread',
        FOREIGN KEY (Sender_ID) REFERENCES USER(User_ID) ON DELETE CASCADE,
        FOREIGN KEY (Receiver_ID) REFERENCES USER(User_ID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS NOTIFICATION (
        Notification_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        User_ID INTEGER NOT NULL,
        Notification_Type TEXT NOT NULL DEFAULT 'General',
        Message TEXT NOT NULL,
        Is_Read BOOLEAN NOT NULL DEFAULT 0,
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (User_ID) REFERENCES USER(User_ID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS FRIEND (
        Friend_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Sender_ID INTEGER NOT NULL,
        Receiver_ID INTEGER NOT NULL,
        Friend_Status TEXT NOT NULL DEFAULT 'Pending',
        Request_Date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Sender_ID) REFERENCES USER(User_ID) ON DELETE CASCADE,
        FOREIGN KEY (Receiver_ID) REFERENCES USER(User_ID) ON DELETE CASCADE,
        UNIQUE (Sender_ID, Receiver_ID)
    );

    CREATE TABLE IF NOT EXISTS RATING_REVIEW (
        Review_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Request_ID INTEGER NOT NULL,
        Reviewer_ID INTEGER NOT NULL,
        Reviewee_ID INTEGER NOT NULL,
        Rating INTEGER NOT NULL CHECK (Rating >= 1 AND Rating <= 5),
        Comment TEXT,
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Request_ID) REFERENCES RIDE_REQUEST(Request_ID) ON DELETE CASCADE,
        FOREIGN KEY (Reviewer_ID) REFERENCES USER(User_ID) ON DELETE CASCADE,
        FOREIGN KEY (Reviewee_ID) REFERENCES USER(User_ID) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS COMMUTE_PASS (
        Pass_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Passenger_ID INTEGER NOT NULL,
        Host_ID INTEGER NOT NULL,
        Source TEXT NOT NULL,
        Destination TEXT NOT NULL,
        Pass_Type TEXT NOT NULL DEFAULT 'Weekly',
        Start_Date DATE NOT NULL,
        End_Date DATE NOT NULL,
        Total_Price REAL NOT NULL,
        Discount_Pct INTEGER NOT NULL DEFAULT 20,
        Pass_Status TEXT NOT NULL DEFAULT 'Active',
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Passenger_ID) REFERENCES USER(User_ID) ON DELETE CASCADE,
        FOREIGN KEY (Host_ID) REFERENCES USER(User_ID) ON DELETE CASCADE
    );

    CREATE TRIGGER IF NOT EXISTS trg_sqlite_after_ride_request_update
    AFTER UPDATE OF Request_Status ON RIDE_REQUEST
    BEGIN
        UPDATE RIDE
        SET Available_Seats = Available_Seats - NEW.Seats_Requested
        WHERE Ride_ID = NEW.Ride_ID AND OLD.Request_Status != 'Accepted' AND NEW.Request_Status = 'Accepted';

        UPDATE RIDE
        SET Available_Seats = Available_Seats + NEW.Seats_Requested
        WHERE Ride_ID = NEW.Ride_ID AND OLD.Request_Status = 'Accepted' AND (NEW.Request_Status = 'Cancelled' OR NEW.Request_Status = 'Rejected');
    END;
    """
    cursor.executescript(schema_script)

    # Seed default sample commuters & rides if database is fresh
    cursor.execute("SELECT COUNT(*) FROM USER")
    if cursor.fetchone()[0] == 0:
        seed_script = """
        INSERT INTO USER (User_ID, Name, Phone_Number, Password, Gender, Profile_Picture, Total_Money_Saved, Average_Rating, Total_Reviews, CO2_Saved_Kg) VALUES
        (1, 'Aishwarya D.', '9876543210', 'pass123', 'Female', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150', 1250.00, 4.95, 12, 45.20),
        (2, 'Rahul Sharma', '9876543211', 'pass123', 'Male', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 840.00, 4.80, 8, 28.50),
        (3, 'Priya Patel', '9876543212', 'pass123', 'Female', 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150', 1600.00, 5.00, 15, 62.00);

        INSERT INTO RIDE (Ride_ID, Driver_ID, Source, Destination, Date, Time, Total_Seats, Available_Seats, Fare_Per_Seat, Total_Cab_Fare, Ride_Type, Vehicle_Info, Is_Women_Only, Estimated_Distance_Km, Ride_Status) VALUES
        (1, 1, 'Thane', 'BKC', '2026-09-10', '08:30:00', 3, 2, 120.00, 480.00, 'Cab_Share', 'Uber XL', 1, 28.0, 'Scheduled'),
        (2, 2, 'Dadar', 'Hinjewadi', '2026-09-11', '09:00:00', 3, 3, 350.00, 1400.00, 'Intercity_Pool', 'Ola Prime Sedan', 0, 140.0, 'Scheduled');

        INSERT INTO STOP (Stop_ID, Ride_ID, Stop_Name, Stop_Order, Arrival_Time, Estimated_Sub_Fare, Latitude, Longitude) VALUES
        (1, 1, 'Mulund Check Naka', 1, '08:45:00', 40.00, 19.1764, 72.9567),
        (2, 1, 'Ghatkopar East (EEH)', 2, '09:05:00', 80.00, 19.0860, 72.9090);
        """
        cursor.executescript(seed_script)

    conn.commit()
    conn.close()
    print("[INFO] Extended database initialized with Pass Auto-Assign, Reviews and Women-Only features.")
