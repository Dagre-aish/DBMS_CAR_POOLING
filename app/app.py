"""
Flask Application for Commuter-First Cab-Sharing & Carpooling DBMS Project
Features:
- Simplified Authentication (Register without email, Login, Logout, Profile)
- 🌸 Female-Only Cab Pools (Women Safety Mode)
- ⭐ 5-Star Rating & Review System with live average calculations
- 🌿 Carbon Footprint & CO2 Emissions Saved Tracker
- 🎫 Weekly / Monthly Commute Pass with Automatic Seat Assignment
- Intelligent En-Route Route & Sub-Trip Matching Engine (e.g. Dadar to Thane matches Dadar to Ulhasnagar)
- Leaflet.js / OpenStreetMap route visualization
- SQL Console & ER business rules (Rule #7 & #8)
"""

import os
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from db import get_db, execute_query, execute_update, get_active_engine, _init_sqlite_db, sync_to_firebase, get_from_firebase

base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))
app.secret_key = os.getenv('SECRET_KEY', 'cabshare_stable_production_secret_key_2026_x89f')
app.config['SESSION_COOKIE_NAME'] = 'cabshare_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Initialize schema if database does not exist
if get_active_engine() == 'sqlite':
    _init_sqlite_db(force_reinit=False)

# Comprehensive Preset Coordinates for Transit Hubs & Localities
COORDINATE_MAP = {
    # Mumbai MMR & Suburban Transit Hubs
    'dadar': {'lat': 19.0178, 'lng': 72.8478, 'name': 'Dadar, Mumbai'},
    'kurla': {'lat': 19.0728, 'lng': 72.8797, 'name': 'Kurla Signal / Phoenix'},
    'ghatkopar': {'lat': 19.0860, 'lng': 72.9090, 'name': 'Ghatkopar East (EEH)'},
    'mulund': {'lat': 19.1764, 'lng': 72.9567, 'name': 'Mulund Check Naka'},
    'thane': {'lat': 19.1872, 'lng': 72.9692, 'name': 'Thane Teen Hath Naka'},
    'dombivli': {'lat': 19.2183, 'lng': 73.0867, 'name': 'Dombivli Kalyan Bypass'},
    'kalyan': {'lat': 19.2403, 'lng': 73.1305, 'name': 'Kalyan Station Road'},
    'ulhasnagar': {'lat': 19.2215, 'lng': 73.1645, 'name': 'Ulhasnagar, Thane'},
    'bandra': {'lat': 19.0596, 'lng': 72.8295, 'name': 'Bandra West, Mumbai'},
    'bkc': {'lat': 19.0662, 'lng': 72.8660, 'name': 'BKC (Maker Maxity), Mumbai'},
    'andheri': {'lat': 19.1136, 'lng': 72.8697, 'name': 'Andheri East, Mumbai'},
    'powai': {'lat': 19.1176, 'lng': 72.9060, 'name': 'Powai Hiranandani, Mumbai'},
    'vashi': {'lat': 19.0770, 'lng': 72.9986, 'name': 'Vashi Toll Plaza, Navi Mumbai'},
    'nerul': {'lat': 19.0330, 'lng': 73.0169, 'name': 'Nerul, Navi Mumbai'},
    'belapur': {'lat': 19.0200, 'lng': 73.0400, 'name': 'CBD Belapur, Navi Mumbai'},
    'kharghar': {'lat': 19.0473, 'lng': 73.0699, 'name': 'Kharghar, Navi Mumbai'},
    'panvel': {'lat': 18.9894, 'lng': 73.1175, 'name': 'Panvel Station Road'},
    'airoli': {'lat': 19.1579, 'lng': 72.9935, 'name': 'Airoli Knowledge Park'},
    'chembur': {'lat': 19.0622, 'lng': 72.8974, 'name': 'Chembur Naka, Mumbai'},
    'sion': {'lat': 19.0402, 'lng': 72.8640, 'name': 'Sion Circle, Mumbai'},
    'worli': {'lat': 19.0166, 'lng': 72.8168, 'name': 'Worli Sea Face'},
    'lower parel': {'lat': 18.9950, 'lng': 72.8300, 'name': 'Lower Parel / High Street Phoenix'},
    'churchgate': {'lat': 18.9322, 'lng': 72.8264, 'name': 'Churchgate, South Mumbai'},
    'colaba': {'lat': 18.9067, 'lng': 72.8147, 'name': 'Colaba, South Mumbai'},
    'cst': {'lat': 18.9400, 'lng': 72.8353, 'name': 'CSMT Station, South Mumbai'},
    'csmt': {'lat': 18.9400, 'lng': 72.8353, 'name': 'CSMT Station, South Mumbai'},
    'goregaon': {'lat': 19.1663, 'lng': 72.8526, 'name': 'Goregaon East (Hub Town)'},
    'malad': {'lat': 19.1860, 'lng': 72.8485, 'name': 'Malad Inorbit Mall'},
    'borivali': {'lat': 19.2307, 'lng': 72.8567, 'name': 'Borivali West, Mumbai'},
    'dahisar': {'lat': 19.2570, 'lng': 72.8650, 'name': 'Dahisar Check Naka'},
    'mira road': {'lat': 19.2812, 'lng': 72.8561, 'name': 'Mira Road East'},
    'bhayandar': {'lat': 19.3017, 'lng': 72.8505, 'name': 'Bhayandar Station Road'},
    'vasai': {'lat': 19.3919, 'lng': 72.8397, 'name': 'Vasai Phata, Highway'},
    'virar': {'lat': 19.4560, 'lng': 72.8060, 'name': 'Virar East, Highway'},

    # Pune Transit Hubs
    'pune': {'lat': 18.5289, 'lng': 73.8744, 'name': 'Pune Railway Station'},
    'hinjewadi': {'lat': 18.5913, 'lng': 73.7389, 'name': 'Hinjewadi IT Park, Pune'},
    'swargate': {'lat': 18.5018, 'lng': 73.8636, 'name': 'Swargate Bus Stand, Pune'},
    'kothrud': {'lat': 18.5074, 'lng': 73.8077, 'name': 'Kothrud Stand, Pune'},
    'baner': {'lat': 18.5590, 'lng': 73.7868, 'name': 'Baner Road, Pune'},
    'wakad': {'lat': 18.5987, 'lng': 73.7688, 'name': 'Wakad Highway Bridge, Pune'},
    'viman nagar': {'lat': 18.5679, 'lng': 73.9143, 'name': 'Viman Nagar, Pune'},
    'hadapsar': {'lat': 18.5089, 'lng': 73.9260, 'name': 'Hadapsar Magarpatta, Pune'},
    'kharadi': {'lat': 18.5515, 'lng': 73.9449, 'name': 'Kharadi EON IT Park, Pune'},

    # Bengaluru Transit Hubs
    'koramangala': {'lat': 12.9352, 'lng': 77.6245, 'name': 'Koramangala, Bengaluru'},
    'silk board': {'lat': 12.9176, 'lng': 77.6238, 'name': 'Silk Board Junction'},
    'electronic city': {'lat': 12.8399, 'lng': 77.6770, 'name': 'Electronic City Phase 1'},
    'hsr layout': {'lat': 12.9121, 'lng': 77.6446, 'name': 'HSR Layout, Bengaluru'},
    'whitefield': {'lat': 12.9698, 'lng': 77.7500, 'name': 'Whitefield ITPL, Bengaluru'},
    'marathahalli': {'lat': 12.9591, 'lng': 77.6974, 'name': 'Marathahalli Bridge'},
    'indiranagar': {'lat': 12.9784, 'lng': 77.6408, 'name': 'Indiranagar 100ft Road'},
    'hebbal': {'lat': 13.0358, 'lng': 77.5970, 'name': 'Hebbal Flyover, Bengaluru'},
    'airport': {'lat': 13.1986, 'lng': 77.7066, 'name': 'Kempegowda Int. Airport'},

    # Delhi NCR
    'delhi': {'lat': 28.6139, 'lng': 77.2090, 'name': 'Connaught Place, New Delhi'},
    'gurgaon': {'lat': 28.4595, 'lng': 77.0266, 'name': 'Cyber City, Gurugram'},
    'gurugram': {'lat': 28.4595, 'lng': 77.0266, 'name': 'Cyber City, Gurugram'},
    'noida': {'lat': 28.5355, 'lng': 77.3910, 'name': 'Noida Sector 62'},
}

_GEOCODE_CACHE = {}

def resolve_coords(location_str):
    """Fuzzy matches location string to geo coordinates with live Nominatim fallback."""
    if not location_str:
        return {'lat': 19.0760, 'lng': 72.8777}
        
    loc_clean = location_str.strip()
    loc_lower = loc_clean.lower()

    # 1. Exact or substring match in preset map
    for key, val in COORDINATE_MAP.items():
        if key == loc_lower or (len(key) > 3 and key in loc_lower):
            return {'lat': val['lat'], 'lng': val['lng']}

    # 2. Check in-memory cache
    if loc_lower in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[loc_lower]

    # 3. Live Geocoding via Nominatim API with fast timeout
    try:
        search_query = loc_clean if ('india' in loc_lower or 'mumbai' in loc_lower or 'pune' in loc_lower or 'bengaluru' in loc_lower) else f"{loc_clean}, India"
        query_encoded = urllib.parse.quote(search_query)
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={query_encoded}&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'CabShareDBMSApp/1.0 (Educational Project)'})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and len(data) > 0:
                coords = {'lat': float(data[0]['lat']), 'lng': float(data[0]['lon'])}
                _GEOCODE_CACHE[loc_lower] = coords
                return coords
    except Exception as e:
        print(f"[WARN] Geocoding lookup fallback failed for '{location_str}': {e}")

    # Fallback to central default if not found
    return {'lat': 19.0760, 'lng': 72.8777}

def ensure_user_in_sqlite(user_dict):
    """Ensures user record exists in local SQLite DB to avoid FK constraint issues on serverless lambdas."""
    if not user_dict or not user_dict.get('User_ID'):
        return
    try:
        existing = execute_query("SELECT User_ID FROM USER WHERE User_ID = %s", (user_dict['User_ID'],), fetchone=True)
        if not existing:
            execute_update("""
                INSERT INTO USER (User_ID, Name, Phone_Number, Password, Gender, Profile_Picture, Total_Money_Saved, Average_Rating, Total_Reviews, CO2_Saved_Kg)
                VALUES (%s, %s, %s, %s, %s, %s, 0.00, 5.00, 0, 0.00)
            """, (
                user_dict['User_ID'],
                user_dict.get('Name', 'Commuter'),
                user_dict.get('Phone_Number', f"90000000{user_dict['User_ID']}"),
                'pass123',
                user_dict.get('Gender', 'Other'),
                user_dict.get('Profile_Picture', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150')
            ))
    except Exception as e:
        print(f"[WARN] ensure_user_in_sqlite error: {e}")

def sync_ride_to_cloud(ride_id):
    """Syncs complete ride, stops, and host info to Firebase Cloud so any Vercel container can read it."""
    try:
        ride = execute_query("""
            SELECT r.*, u.Name as Driver_Name, u.Phone_Number as Driver_Phone, u.Profile_Picture as Driver_Avatar, u.Average_Rating, u.Gender as Driver_Gender
            FROM RIDE r
            JOIN USER u ON r.Driver_ID = u.User_ID
            WHERE r.Ride_ID = %s
        """, (ride_id,), fetchone=True)
        if not ride:
            return
        stops = execute_query("SELECT * FROM STOP WHERE Ride_ID = %s ORDER BY Stop_Order ASC", (ride_id,))
        payload = dict(ride)
        payload['stops'] = stops or []
        sync_to_firebase(f"rides/{ride_id}", payload)
    except Exception as e:
        print(f"[WARN] sync_ride_to_cloud error: {e}")

def restore_ride_from_cloud(ride_id):
    """Restores a missing ride from Firebase Cloud into local SQLite DB if container was cold-started."""
    try:
        fb_ride = get_from_firebase(f"rides/{ride_id}")
        if not fb_ride or not isinstance(fb_ride, dict):
            return None
        
        driver_id = fb_ride.get('Driver_ID') or 1
        driver_user = {
            'User_ID': driver_id,
            'Name': fb_ride.get('Driver_Name', 'Host Commuter'),
            'Phone_Number': fb_ride.get('Driver_Phone', '9876543210'),
            'Gender': fb_ride.get('Driver_Gender', 'Other'),
            'Profile_Picture': fb_ride.get('Driver_Avatar', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150'),
            'Average_Rating': fb_ride.get('Average_Rating', 5.0)
        }
        ensure_user_in_sqlite(driver_user)

        execute_update("""
            INSERT OR IGNORE INTO RIDE (Ride_ID, Driver_ID, Source, Destination, Date, Time, Total_Seats, Available_Seats, Fare_Per_Seat, Total_Cab_Fare, Ride_Type, Vehicle_Info, Is_Women_Only, Estimated_Distance_Km, Ride_Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ride_id,
            driver_id,
            fb_ride.get('Source', 'CST'),
            fb_ride.get('Destination', 'Virar'),
            fb_ride.get('Date', str(datetime.now().date())),
            fb_ride.get('Time', '09:00:00'),
            fb_ride.get('Total_Seats', 3),
            fb_ride.get('Available_Seats', 3),
            fb_ride.get('Fare_Per_Seat', 150.0),
            fb_ride.get('Total_Cab_Fare', 600.0),
            fb_ride.get('Ride_Type', 'Cab_Share'),
            fb_ride.get('Vehicle_Info', 'Uber XL / Ola Prime'),
            1 if fb_ride.get('Is_Women_Only') else 0,
            fb_ride.get('Estimated_Distance_Km', 25.0),
            fb_ride.get('Ride_Status', 'Scheduled')
        ))

        execute_update("UPDATE RIDE SET Available_Seats = %s, Ride_Status = %s WHERE Ride_ID = %s",
                       (fb_ride.get('Available_Seats', 3), fb_ride.get('Ride_Status', 'Scheduled'), ride_id))

        for s in fb_ride.get('stops', []):
            if isinstance(s, dict) and s.get('Stop_Name'):
                execute_update("""
                    INSERT OR IGNORE INTO STOP (Stop_ID, Ride_ID, Stop_Name, Stop_Order, Arrival_Time, Estimated_Sub_Fare, Latitude, Longitude)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    s.get('Stop_ID'),
                    ride_id,
                    s.get('Stop_Name', 'Waystation'),
                    s.get('Stop_Order', 1),
                    s.get('Arrival_Time'),
                    s.get('Estimated_Sub_Fare', 0.0),
                    s.get('Latitude'),
                    s.get('Longitude')
                ))

        return execute_query("""
            SELECT r.*, u.Name as Driver_Name, u.Phone_Number as Driver_Phone, u.Profile_Picture as Driver_Avatar, u.Average_Rating, u.Total_Reviews
            FROM RIDE r
            JOIN USER u ON r.Driver_ID = u.User_ID
            WHERE r.Ride_ID = %s
        """, (ride_id,), fetchone=True)
    except Exception as e:
        print(f"[WARN] restore_ride_from_cloud error: {e}")
        return None

def sync_all_cloud_rides():
    """Fetches all rides from Firebase Cloud and restores missing rides to SQLite for search/listing."""
    try:
        all_cloud = get_from_firebase("rides")
        if not all_cloud or not isinstance(all_cloud, dict):
            return
        for r_id_str, fb_ride in all_cloud.items():
            if isinstance(fb_ride, dict) and fb_ride.get('Ride_ID'):
                restore_ride_from_cloud(fb_ride['Ride_ID'])
    except Exception as e:
        print(f"[WARN] sync_all_cloud_rides error: {e}")

def sync_request_to_cloud(request_id):
    """Syncs a ride request and passenger info to Firebase Cloud so all serverless lambdas stay updated."""
    try:
        req = execute_query("""
            SELECT rr.*, p.Name as Passenger_Name, p.Phone_Number as Passenger_Phone, p.Profile_Picture as Passenger_Avatar, p.Gender as Passenger_Gender,
                   r.Driver_ID, r.Source, r.Destination, r.Date, r.Time
            FROM RIDE_REQUEST rr
            JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
            JOIN USER p ON rr.User_ID = p.User_ID
            WHERE rr.Request_ID = %s
        """, (request_id,), fetchone=True)
        if not req:
            return
        payload = dict(req)
        sync_to_firebase(f"requests/{request_id}", payload)
    except Exception as e:
        print(f"[WARN] sync_request_to_cloud error: {e}")

def restore_request_from_cloud(request_id):
    """Restores a missing ride request from Firebase Cloud into local SQLite DB."""
    try:
        fb_req = get_from_firebase(f"requests/{request_id}")
        if not fb_req or not isinstance(fb_req, dict):
            return None
        
        user_id = fb_req.get('User_ID')
        ride_id = fb_req.get('Ride_ID')
        if not user_id or not ride_id:
            return None

        # Ensure passenger user exists in SQLite
        ensure_user_in_sqlite({
            'User_ID': user_id,
            'Name': fb_req.get('Passenger_Name', 'Commuter'),
            'Phone_Number': fb_req.get('Passenger_Phone', f'90000000{user_id}'),
            'Gender': fb_req.get('Passenger_Gender', 'Other'),
            'Profile_Picture': fb_req.get('Passenger_Avatar', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150')
        })
        
        # Ensure ride exists in SQLite
        restore_ride_from_cloud(ride_id)
        
        # Insert or replace request in local SQLite
        execute_update("""
            INSERT OR REPLACE INTO RIDE_REQUEST (Request_ID, User_ID, Ride_ID, Pickup_Point, Dropoff_Point, Seats_Requested, Agreed_Fare, Request_Status, Request_Time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request_id,
            user_id,
            ride_id,
            fb_req.get('Pickup_Point'),
            fb_req.get('Dropoff_Point'),
            fb_req.get('Seats_Requested', 1),
            fb_req.get('Agreed_Fare', 0.0),
            fb_req.get('Request_Status', 'Pending'),
            fb_req.get('Request_Time', str(datetime.now()))
        ))

        return execute_query("""
            SELECT rr.*, p.Name as Passenger_Name, p.Phone_Number as Passenger_Phone, p.Profile_Picture as Passenger_Avatar, p.Gender as Passenger_Gender,
                   r.Driver_ID, r.Source, r.Destination, r.Date, r.Time
            FROM RIDE_REQUEST rr
            JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
            JOIN USER p ON rr.User_ID = p.User_ID
            WHERE rr.Request_ID = %s
        """, (request_id,), fetchone=True)
    except Exception as e:
        print(f"[WARN] restore_request_from_cloud error: {e}")
        return None

def sync_all_cloud_requests():
    """Fetches all ride requests from Firebase Cloud and restores missing ones to local SQLite."""
    try:
        all_reqs = get_from_firebase("requests")
        if not all_reqs or not isinstance(all_reqs, dict):
            return
        for req_id_str, fb_req in all_reqs.items():
            if isinstance(fb_req, dict) and fb_req.get('Request_ID'):
                restore_request_from_cloud(fb_req['Request_ID'])
    except Exception as e:
        print(f"[WARN] sync_all_cloud_requests error: {e}")

def sync_chat_msg_to_cloud(chat_id, request_id, sender_id, receiver_id, message, sent_time, seen_status='Unread', chat_key=None):
    """Syncs chat message to Firebase Cloud."""
    try:
        msg_payload = {
            'Chat_ID': chat_id,
            'Request_ID': request_id,
            'Sender_ID': sender_id,
            'Receiver_ID': receiver_id,
            'Message': message,
            'Sent_Time': str(sent_time),
            'Seen_Status': seen_status
        }
        if request_id:
            sync_to_firebase(f"ride_chats/{request_id}/{chat_id}", msg_payload)
        if chat_key:
            sync_to_firebase(f"friend_chats/{chat_key}/{chat_id}", msg_payload)
    except Exception as e:
        print(f"[WARN] sync_chat_msg_to_cloud error: {e}")

def restore_chats_from_cloud(request_id=None, chat_key=None):
    """Restores missing chat messages from Firebase Cloud into local SQLite."""
    try:
        cloud_msgs = None
        if request_id:
            cloud_msgs = get_from_firebase(f"ride_chats/{request_id}")
        elif chat_key:
            cloud_msgs = get_from_firebase(f"friend_chats/{chat_key}")
            
        if not cloud_msgs or not isinstance(cloud_msgs, dict):
            return
            
        for c_id_str, fb_msg in cloud_msgs.items():
            if isinstance(fb_msg, dict) and fb_msg.get('Sender_ID') and fb_msg.get('Receiver_ID'):
                c_id = fb_msg.get('Chat_ID')
                sender_id = fb_msg['Sender_ID']
                receiver_id = fb_msg['Receiver_ID']
                req_id = fb_msg.get('Request_ID') or request_id
                
                ensure_user_in_sqlite({'User_ID': sender_id})
                ensure_user_in_sqlite({'User_ID': receiver_id})
                
                if c_id:
                    execute_update("""
                        INSERT OR IGNORE INTO CHAT (Chat_ID, Request_ID, Sender_ID, Receiver_ID, Message, Sent_Time, Seen_Status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        c_id,
                        req_id,
                        sender_id,
                        receiver_id,
                        fb_msg.get('Message', ''),
                        fb_msg.get('Sent_Time', str(datetime.now())),
                        fb_msg.get('Seen_Status', 'Unread')
                    ))
                else:
                    execute_update("""
                        INSERT INTO CHAT (Request_ID, Sender_ID, Receiver_ID, Message, Sent_Time, Seen_Status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        req_id,
                        sender_id,
                        receiver_id,
                        fb_msg.get('Message', ''),
                        fb_msg.get('Sent_Time', str(datetime.now())),
                        fb_msg.get('Seen_Status', 'Unread')
                    ))
    except Exception as e:
        print(f"[WARN] restore_chats_from_cloud error: {e}")

# Helper: Active User Management
def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    try:
        user = execute_query("SELECT * FROM USER WHERE User_ID = %s", (uid,), fetchone=True)
    except Exception:
        user = None

    if not user and session.get('user_name'):
        user = {
            'User_ID': session.get('user_id'),
            'Name': session.get('user_name', 'Commuter'),
            'Phone_Number': session.get('user_phone', '9876543210'),
            'Gender': session.get('user_gender', 'Other'),
            'Profile_Picture': session.get('user_avatar', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150'),
            'Total_Money_Saved': 0.00,
            'Average_Rating': 5.00,
            'Total_Reviews': 0,
            'CO2_Saved_Kg': 0.00
        }
        ensure_user_in_sqlite(user)
    return user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in or create an account to perform this action.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_global_data():
    current_user = get_current_user()
    unread_count = 0
    if current_user and current_user.get('User_ID'):
        try:
            res = execute_query(
                "SELECT COUNT(*) as count FROM NOTIFICATION WHERE User_ID = %s AND Is_Read = 0",
                (current_user['User_ID'],),
                fetchone=True
            )
            if res:
                unread_count = res.get('count', 0)
        except Exception:
            unread_count = 0
    
    try:
        all_users = execute_query("SELECT User_ID, Name, Phone_Number, Gender, Profile_Picture, Total_Money_Saved, Average_Rating, CO2_Saved_Kg FROM USER ORDER BY User_ID ASC")
    except Exception:
        all_users = []
    engine = get_active_engine()
    return dict(current_user=current_user, unread_notifications=unread_count, all_users=all_users, active_engine=engine)

# ============================================================================
# 1. AUTHENTICATION (REGISTER, LOGIN, LOGOUT, PROFILE)
# ============================================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone_number', '').strip()
        password = request.form.get('password', '').strip()
        gender = request.form.get('gender', 'Other')

        if not name or not phone or not password:
            flash("Please fill in Name, Phone Number, and Password.", "danger")
            return redirect(url_for('register'))

        existing = execute_query("SELECT User_ID FROM USER WHERE Phone_Number = %s", (phone,), fetchone=True)
        if existing:
            flash("An account with this phone number already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        avatar = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150" if gender == 'Female' else "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"

        try:
            user_id, _ = execute_update("""
                INSERT INTO USER (Name, Phone_Number, Password, Gender, Profile_Picture, Total_Money_Saved, Average_Rating, Total_Reviews, CO2_Saved_Kg)
                VALUES (%s, %s, %s, %s, %s, 0.00, 5.00, 0, 0.00)
            """, (name, phone, password, gender, avatar))

            # Sync User Account to Firebase Cloud for cross-container serverless persistence
            sync_to_firebase(f"users/{phone}", {
                'user_id': user_id,
                'name': name,
                'phone': phone,
                'password': password,
                'gender': gender,
                'avatar': avatar
            })

            session.permanent = True
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_phone'] = phone
            session['user_gender'] = gender
            session['user_avatar'] = avatar
            flash(f"Welcome, {name}! Your commuter account was created successfully.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Could not create account: {e}", "danger")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and session.get('user_id'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        phone = request.form.get('phone_number', '').strip()
        password = request.form.get('password', '').strip()

        if not phone or not password:
            flash("Please fill in both Phone Number and Password.", "danger")
            return redirect(url_for('login'))

        # 1. Primary DB lookup
        user = execute_query(
            "SELECT * FROM USER WHERE Phone_Number = %s AND Password = %s",
            (phone, password),
            fetchone=True
        )

        # 2. Fallback for pre-seeded demo accounts if container DB is fresh
        if not user and password == 'pass123':
            seed_accounts = {
                '9876543210': {'user_id': 1, 'name': 'Aishwarya D.', 'gender': 'Female', 'avatar': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150'},
                '9876543211': {'user_id': 2, 'name': 'Rahul Sharma', 'gender': 'Male', 'avatar': 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150'},
                '9876543212': {'user_id': 3, 'name': 'Priya Patel', 'gender': 'Female', 'avatar': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150'}
            }
            if phone in seed_accounts:
                info = seed_accounts[phone]
                try:
                    execute_update("""
                        INSERT OR IGNORE INTO USER (User_ID, Name, Phone_Number, Password, Gender, Profile_Picture, Total_Money_Saved, Average_Rating, Total_Reviews, CO2_Saved_Kg)
                        VALUES (%s, %s, %s, %s, %s, %s, 1250.00, 4.95, 12, 45.20)
                    """, (info['user_id'], info['name'], phone, password, info['gender'], info['avatar']))
                except Exception:
                    pass
                user = execute_query("SELECT * FROM USER WHERE Phone_Number = %s", (phone,), fetchone=True)

        # 3. Fallback to Firebase Cloud DB if user registered on another container
        if not user:
            fb_user = get_from_firebase(f"users/{phone}")
            if fb_user and str(fb_user.get('password')) == str(password):
                try:
                    execute_update("""
                        INSERT OR IGNORE INTO USER (Name, Phone_Number, Password, Gender, Profile_Picture, Total_Money_Saved, Average_Rating, Total_Reviews, CO2_Saved_Kg)
                        VALUES (%s, %s, %s, %s, %s, 0.00, 5.00, 0, 0.00)
                    """, (fb_user.get('name', 'Commuter'), phone, password, fb_user.get('gender', 'Other'), fb_user.get('avatar', '')))
                except Exception:
                    pass
                user = execute_query(
                    "SELECT * FROM USER WHERE Phone_Number = %s AND Password = %s",
                    (phone, password),
                    fetchone=True
                )

        if user:
            session.clear()
            session.permanent = True
            session['user_id'] = user['User_ID']
            session['user_name'] = user['Name']
            session['user_phone'] = user['Phone_Number']
            session['user_gender'] = user['Gender']
            session['user_avatar'] = user.get('Profile_Picture', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150')
            flash(f"Welcome back, {user['Name']}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash(f"Invalid phone number or password. Click one of the Instant Demo Login buttons below!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    
    rides_hosted = execute_query(
        "SELECT * FROM RIDE WHERE Driver_ID = %s ORDER BY Created_At DESC",
        (user['User_ID'],)
    )

    rides_joined = execute_query("""
        SELECT rr.*, r.Source, r.Destination, r.Date, r.Time
        FROM RIDE_REQUEST rr
        JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
        WHERE rr.User_ID = %s
        ORDER BY rr.Request_Time DESC
    """, (user['User_ID'],))

    # User reviews received
    reviews_received = execute_query("""
        SELECT rv.*, u.Name as Reviewer_Name, u.Profile_Picture as Reviewer_Avatar
        FROM RATING_REVIEW rv
        JOIN USER u ON rv.Reviewer_ID = u.User_ID
        WHERE rv.Reviewee_ID = %s
        ORDER BY rv.Created_At DESC
    """, (user['User_ID'],))

    friends_res = execute_query("""
        SELECT COUNT(*) as count FROM FRIEND 
        WHERE (Sender_ID = %s OR Receiver_ID = %s) AND Friend_Status = 'Accepted'
    """, (user['User_ID'], user['User_ID']), fetchone=True)
    friends_count = friends_res['count'] if friends_res else 0

    return render_template('profile.html',
                           rides_hosted=rides_hosted,
                           rides_joined=rides_joined,
                           reviews_received=reviews_received,
                           friends_count=friends_count)

# ============================================================================
# 2. COMMUTER DASHBOARD
# ============================================================================
@app.route('/')
def index():
    user = get_current_user()
    
    total_users = execute_query("SELECT COUNT(*) as count FROM USER", fetchone=True)['count']
    active_rides = execute_query("SELECT COUNT(*) as count FROM RIDE WHERE Ride_Status = 'Scheduled'", fetchone=True)['count']
    total_bookings = execute_query("SELECT COUNT(*) as count FROM RIDE_REQUEST WHERE Request_Status = 'Accepted'", fetchone=True)['count']
    total_savings = execute_query("SELECT COALESCE(SUM(Total_Money_Saved), 0) as total FROM USER", fetchone=True)['total']
    total_co2 = execute_query("SELECT COALESCE(SUM(CO2_Saved_Kg), 0) as total FROM USER", fetchone=True)['total']

    featured_rides = execute_query("""
        SELECT r.*, u.Name as Driver_Name, u.Profile_Picture as Driver_Avatar, u.Average_Rating,
               (SELECT COUNT(*) FROM STOP s WHERE s.Ride_ID = r.Ride_ID) as Total_Stops,
               (SELECT GROUP_CONCAT(s2.Stop_Name, ' ➔ ') FROM STOP s2 WHERE s2.Ride_ID = r.Ride_ID) as Stops_List
        FROM RIDE r
        JOIN USER u ON r.Driver_ID = u.User_ID
        WHERE r.Ride_Status = 'Scheduled'
        ORDER BY r.Date ASC, r.Time ASC
        LIMIT 6
    """)

    top_savers = execute_query("""
        SELECT u.User_ID, u.Name, u.Profile_Picture, u.Total_Money_Saved, u.Average_Rating, u.CO2_Saved_Kg,
               (SELECT COUNT(*) FROM RIDE_REQUEST rr WHERE rr.User_ID = u.User_ID AND rr.Request_Status = 'Accepted') as Trips_Shared
        FROM USER u
        ORDER BY u.Total_Money_Saved DESC
        LIMIT 5
    """)

    return render_template('index.html',
                           total_users=total_users,
                           active_rides=active_rides,
                           total_bookings=total_bookings,
                           total_savings=total_savings,
                           total_co2=total_co2,
                           featured_rides=featured_rides,
                           top_savers=top_savers)

# ============================================================================
# 3. INTELLIGENT EN-ROUTE RIDE SEARCH & MATCHER
# ============================================================================
@app.route('/rides')
def rides_list():
    sync_all_cloud_rides()
    search_source = request.args.get('source', '').strip()
    search_dest = request.args.get('destination', '').strip()
    travel_date = request.args.get('date', '').strip()
    min_seats = request.args.get('seats', '').strip()
    women_only = request.args.get('women_only', '').strip()

    sql = """
        SELECT r.*, u.Name as Driver_Name, u.Phone_Number as Driver_Phone, u.Profile_Picture as Driver_Avatar, u.Average_Rating, u.Gender as Driver_Gender
        FROM RIDE r
        JOIN USER u ON r.Driver_ID = u.User_ID
        WHERE r.Ride_Status = 'Scheduled'
    """
    params = []

    if travel_date:
        sql += " AND r.Date = %s"
        params.append(travel_date)
    if min_seats:
        sql += " AND r.Available_Seats >= %s"
        params.append(int(min_seats))
    if women_only == '1':
        sql += " AND r.Is_Women_Only = 1"

    sql += " ORDER BY r.Date ASC, r.Time ASC"
    all_rides = execute_query(sql, tuple(params) if params else None)

    matched_results = []

    for ride in all_rides:
        stops = execute_query(
            "SELECT * FROM STOP WHERE Ride_ID = %s ORDER BY Stop_Order ASC",
            (ride['Ride_ID'],)
        )
        ride['stops'] = stops
        ride['total_stops_count'] = len(stops)

        itinerary = []
        itinerary.append({
            'type': 'origin',
            'order': 0,
            'name': ride['Source'],
            'time': ride['Time'],
            'sub_fare': 0.0
        })
        for s in stops:
            itinerary.append({
                'type': 'stop',
                'order': s['Stop_Order'],
                'name': s['Stop_Name'],
                'time': s['Arrival_Time'],
                'sub_fare': float(s['Estimated_Sub_Fare'] or 0.0)
            })
        itinerary.append({
            'type': 'destination',
            'order': len(stops) + 1,
            'name': ride['Destination'],
            'time': None,
            'sub_fare': float(ride['Fare_Per_Seat'])
        })
        ride['itinerary'] = itinerary

        if not search_source and not search_dest:
            ride['is_enroute_match'] = False
            ride['match_pickup'] = ride['Source']
            ride['match_dropoff'] = ride['Destination']
            ride['computed_sub_fare'] = float(ride['Fare_Per_Seat'])
            ride['solo_cab_estimated'] = float(ride['Total_Cab_Fare'] or ride['Fare_Per_Seat'] * 3.5)
            ride['money_saved'] = max(0, ride['solo_cab_estimated'] - ride['computed_sub_fare'])
            matched_results.append(ride)
            continue

        src_lower = search_source.lower() if search_source else ''
        dest_lower = search_dest.lower() if search_dest else ''

        pickup_match_idx = None
        dropoff_match_idx = None
        pickup_name = ride['Source']
        dropoff_name = ride['Destination']

        if src_lower:
            for idx, pt in enumerate(itinerary):
                if src_lower in pt['name'].lower():
                    pickup_match_idx = idx
                    pickup_name = pt['name']
                    break
        else:
            pickup_match_idx = 0

        if dest_lower:
            for idx, pt in enumerate(itinerary):
                if dest_lower in pt['name'].lower():
                    dropoff_match_idx = idx
                    dropoff_name = pt['name']
                    break
        else:
            dropoff_match_idx = len(itinerary) - 1

        if (pickup_match_idx is not None) and (dropoff_match_idx is not None) and (pickup_match_idx < dropoff_match_idx):
            is_direct = (pickup_match_idx == 0 and dropoff_match_idx == len(itinerary) - 1)
            ride['is_enroute_match'] = not is_direct
            ride['match_pickup'] = pickup_name
            ride['match_dropoff'] = dropoff_name

            drop_sub_fare = itinerary[dropoff_match_idx]['sub_fare']
            pickup_sub_fare = itinerary[pickup_match_idx]['sub_fare']
            
            if drop_sub_fare > 0 and drop_sub_fare >= pickup_sub_fare:
                computed_fare = drop_sub_fare - pickup_sub_fare
                if computed_fare <= 0:
                    computed_fare = float(ride['Fare_Per_Seat']) * 0.5
            else:
                fraction = (dropoff_match_idx - pickup_match_idx) / (len(itinerary) - 1)
                computed_fare = round(float(ride['Fare_Per_Seat']) * max(0.3, fraction), 0)

            ride['computed_sub_fare'] = max(30.0, computed_fare)
            ride['solo_cab_estimated'] = ride['computed_sub_fare'] * 3.2
            ride['money_saved'] = ride['solo_cab_estimated'] - ride['computed_sub_fare']

            matched_results.append(ride)

    return render_template('rides.html',
                           rides=matched_results,
                           source=search_source,
                           destination=search_dest,
                           date=travel_date,
                           seats=min_seats,
                           women_only=women_only)

# ============================================================================
# 4. RIDE DETAIL & INTERACTIVE LEAFLET MAP
# ============================================================================
@app.route('/rides/<int:ride_id>')
def ride_detail(ride_id):
    user = get_current_user()
    ride = execute_query("""
        SELECT r.*, u.Name as Driver_Name, u.Phone_Number as Driver_Phone, u.Profile_Picture as Driver_Avatar, u.Average_Rating, u.Total_Reviews
        FROM RIDE r
        JOIN USER u ON r.Driver_ID = u.User_ID
        WHERE r.Ride_ID = %s
    """, (ride_id,), fetchone=True)

    if not ride:
        ride = restore_ride_from_cloud(ride_id)

    if not ride:
        flash("Cab-share listing not found.", "danger")
        return redirect(url_for('rides_list'))

    stops = execute_query("SELECT * FROM STOP WHERE Ride_ID = %s ORDER BY Stop_Order ASC", (ride_id,))
    
    map_waypoints = []
    start_c = resolve_coords(ride['Source'])
    map_waypoints.append({'name': ride['Source'], 'lat': start_c['lat'], 'lng': start_c['lng'], 'type': 'Start'})

    for s in stops:
        if s.get('Latitude') and s.get('Longitude'):
            s_lat, s_lng = float(s['Latitude']), float(s['Longitude'])
        else:
            c = resolve_coords(s['Stop_Name'])
            s_lat, s_lng = c['lat'], c['lng']
        map_waypoints.append({
            'name': f"Stop {s['Stop_Order']}: {s['Stop_Name']}",
            'lat': s_lat,
            'lng': s_lng,
            'time': s['Arrival_Time'],
            'fare': s['Estimated_Sub_Fare'],
            'type': 'Waypoint'
        })

    end_c = resolve_coords(ride['Destination'])
    map_waypoints.append({'name': ride['Destination'], 'lat': end_c['lat'], 'lng': end_c['lng'], 'type': 'End'})

    requests = execute_query("""
        SELECT rr.*, p.Name as Passenger_Name, p.Phone_Number as Passenger_Phone, p.Profile_Picture as Passenger_Avatar,
               (SELECT COUNT(*) FROM RATING_REVIEW rv WHERE rv.Request_ID = rr.Request_ID AND rv.Reviewer_ID = %s) as Has_Reviewed
        FROM RIDE_REQUEST rr
        JOIN USER p ON rr.User_ID = p.User_ID
        WHERE rr.Ride_ID = %s
        ORDER BY rr.Request_Time DESC
    """, (user['User_ID'] if user else 0, ride_id))

    user_request = None
    if user:
        user_request = execute_query("""
            SELECT rr.*,
                   (SELECT COUNT(*) FROM RATING_REVIEW rv WHERE rv.Request_ID = rr.Request_ID AND rv.Reviewer_ID = %s) as Has_Reviewed
            FROM RIDE_REQUEST rr
            WHERE rr.Ride_ID = %s AND rr.User_ID = %s
        """, (user['User_ID'], ride_id, user['User_ID']), fetchone=True)

    solo_cab_cost = float(ride['Total_Cab_Fare']) if ride['Total_Cab_Fare'] > 0 else float(ride['Fare_Per_Seat']) * 3.5
    cost_per_person = float(ride['Fare_Per_Seat'])
    savings_per_seat = max(0, solo_cab_cost - cost_per_person)
    savings_pct = round((savings_per_seat / solo_cab_cost) * 100, 0) if solo_cab_cost > 0 else 0

    return render_template('ride_detail.html',
                           ride=ride,
                           stops=stops,
                           map_waypoints=map_waypoints,
                           requests=requests,
                           user_request=user_request,
                           solo_cab_cost=solo_cab_cost,
                           cost_per_person=cost_per_person,
                           savings_per_seat=savings_per_seat,
                           savings_pct=savings_pct)

@app.route('/rides/<int:ride_id>/complete', methods=['POST'])
@login_required
def complete_ride(ride_id):
    user = get_current_user()
    ride = execute_query("SELECT * FROM RIDE WHERE Ride_ID = %s", (ride_id,), fetchone=True)

    if not ride:
        flash("Cab pool listing not found.", "danger")
        return redirect(url_for('rides_list'))

    if ride['Driver_ID'] != user['User_ID']:
        flash("Unauthorized: Only the pool host can complete this ride.", "danger")
        return redirect(url_for('ride_detail', ride_id=ride_id))

    if ride['Ride_Status'] == 'Completed':
        flash("This cab pool is already marked as completed.", "info")
        return redirect(url_for('ride_detail', ride_id=ride_id))

    execute_update("UPDATE RIDE SET Ride_Status = 'Completed' WHERE Ride_ID = %s", (ride_id,))

    # Notify all accepted co-commuters to rate/review the trip
    accepted_commuters = execute_query("""
        SELECT User_ID FROM RIDE_REQUEST
        WHERE Ride_ID = %s AND Request_Status = 'Accepted'
    """, (ride_id,))

    for c in accepted_commuters:
        execute_update("""
            INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
            VALUES (%s, 'General', %s, 0)
        """, (c['User_ID'], f"🎉 Ride #{ride_id} ({ride['Source']} -> {ride['Destination']}) has been marked as Completed! Please rate & review your host and co-commuters."))

    flash("🎉 Cab pool marked as Completed! You can now rate and review your co-commuters below.", "success")
    return redirect(request.referrer or url_for('ride_detail', ride_id=ride_id))

# ============================================================================
# 5. POST CAB-SHARE + MULTI-WAYPOINTS + PASS AUTO-ASSIGNMENT ENGINE
# ============================================================================
@app.route('/rides/create', methods=['GET', 'POST'])
@login_required
def create_ride():
    user = get_current_user()
    ensure_user_in_sqlite(user)
    if request.method == 'POST':
        source = request.form.get('source', '').strip()
        destination = request.form.get('destination', '').strip()
        travel_date = request.form.get('date')
        travel_time = request.form.get('time')
        total_seats = int(request.form.get('total_seats', 3))
        ride_type = request.form.get('ride_type', 'Cab_Share')
        vehicle_info = request.form.get('vehicle_info', 'Uber XL / Ola Prime').strip()
        is_women_only = 1 if request.form.get('is_women_only') else 0
        total_cab_fare = float(request.form.get('total_cab_fare', 600.0))
        fare_per_seat = float(request.form.get('fare_per_seat', total_cab_fare / (total_seats + 1)))
        distance_km = float(request.form.get('distance_km', 25.0))

        if not source or not destination or not travel_date or not travel_time:
            flash("Please fill in all mandatory fields.", "danger")
            return redirect(url_for('create_ride'))

        ride_id, _ = execute_update("""
            INSERT INTO RIDE (Driver_ID, Source, Destination, Date, Time, Total_Seats, Available_Seats, Fare_Per_Seat, Total_Cab_Fare, Ride_Type, Vehicle_Info, Is_Women_Only, Estimated_Distance_Km, Ride_Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Scheduled')
        """, (user['User_ID'], source, destination, travel_date, travel_time, total_seats, total_seats, fare_per_seat, total_cab_fare, ride_type, vehicle_info, is_women_only, distance_km))

        stop_names = request.form.getlist('stop_name[]')
        stop_times = request.form.getlist('stop_time[]')
        stop_fares = request.form.getlist('stop_fare[]')

        order = 1
        for idx in range(len(stop_names)):
            s_name = stop_names[idx].strip() if idx < len(stop_names) else ''
            s_time = stop_times[idx] if idx < len(stop_times) else None
            s_fare = float(stop_fares[idx]) if idx < len(stop_fares) and stop_fares[idx] else (fare_per_seat * (order / (len(stop_names) + 1)))

            if s_name:
                coords = resolve_coords(s_name)
                execute_update("""
                    INSERT INTO STOP (Ride_ID, Stop_Name, Stop_Order, Arrival_Time, Estimated_Sub_Fare, Latitude, Longitude)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (ride_id, s_name, order, s_time if s_time else None, s_fare, coords['lat'], coords['lng']))
                order += 1

        # ====================================================================
        # AUTOMATIC SEAT ASSIGNMENT ENGINE FOR PASS HOLDERS
        # ====================================================================
        active_passes = execute_query("""
            SELECT cp.*, u.Name as Passenger_Name
            FROM COMMUTE_PASS cp
            JOIN USER u ON cp.Passenger_ID = u.User_ID
            WHERE cp.Host_ID = %s 
              AND cp.Pass_Status = 'Active'
              AND cp.Start_Date <= %s AND cp.End_Date >= %s
        """, (user['User_ID'], travel_date, travel_date))

        current_avail = total_seats
        auto_assigned_count = 0

        for p in active_passes:
            if current_avail > 0:
                # Auto book seat
                execute_update("""
                    INSERT INTO RIDE_REQUEST (User_ID, Ride_ID, Pickup_Point, Dropoff_Point, Seats_Requested, Agreed_Fare, Request_Status)
                    VALUES (%s, %s, %s, %s, 1, 0.00, 'Accepted')
                """, (p['Passenger_ID'], ride_id, p['Source'], p['Destination']))

                current_avail -= 1
                auto_assigned_count += 1

                # Update seats on ride
                execute_update("UPDATE RIDE SET Available_Seats = %s WHERE Ride_ID = %s", (current_avail, ride_id))

                # Notify Passenger
                execute_update("""
                    INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
                    VALUES (%s, 'Request_Accepted', %s, 0)
                """, (p['Passenger_ID'], f"🎫 Pass Auto-Assigned! Your active {p['Pass_Type']} Pass reserved a seat on {user['Name']}'s ride for {travel_date} ({source} -> {destination})."))

                # Notify Host
                execute_update("""
                    INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
                    VALUES (%s, 'General', %s, 0)
                """, (user['User_ID'], f"🎫 Pass Auto-Booking: {p['Passenger_Name']} was automatically assigned a seat via their {p['Pass_Type']} Pass."))

        if auto_assigned_count > 0:
            flash(f"Cab route published! {auto_assigned_count} Commute Pass holder(s) were automatically assigned confirmed seats.", "success")
        else:
            flash("Cab-share route created with multiple pickup/drop waypoints!", "success")
            
        sync_ride_to_cloud(ride_id)
        sync_to_firebase('live_events', {
            'event': 'ride_created',
            'ride_id': ride_id,
            'source': source,
            'destination': destination,
            'driver_id': user['User_ID'],
            'driver_name': user['Name'],
            'timestamp': int(time.time())
        })

        return redirect(url_for('ride_detail', ride_id=ride_id))

    return render_template('create_ride.html')

# ============================================================================
# 6. BOOKING / FARE-SPLIT REQUESTS (BUSINESS RULE #8 & WOMEN-ONLY CHECK)
# ============================================================================
@app.route('/rides/<int:ride_id>/request', methods=['POST'])
@login_required
def request_ride(ride_id):
    user = get_current_user()
    seats_requested = int(request.form.get('seats_requested', 1))
    pickup_point = request.form.get('pickup_point', '').strip()
    dropoff_point = request.form.get('dropoff_point', '').strip()
    agreed_fare = float(request.form.get('agreed_fare', 0.0))

    ride = execute_query("SELECT * FROM RIDE WHERE Ride_ID = %s", (ride_id,), fetchone=True)
    if not ride:
        ride = restore_ride_from_cloud(ride_id)

    if not ride:
        flash("Ride not found.", "danger")
        return redirect(url_for('rides_list'))

    if ride['Driver_ID'] == user['User_ID']:
        flash("You cannot request seats on a commute pool you created.", "warning")
        return redirect(url_for('ride_detail', ride_id=ride_id))

    # Feature 1 Check: Women-Only Pool Security
    if ride.get('Is_Women_Only') and user['Gender'] != 'Female':
        flash("🌸 Access Denied: This is a verified Women-Only Cab Pool. Only female commuters can request seats.", "danger")
        return redirect(url_for('ride_detail', ride_id=ride_id))

    if seats_requested > ride['Available_Seats']:
        flash(f"Only {ride['Available_Seats']} seats available. Cannot request {seats_requested}.", "danger")
        return redirect(url_for('ride_detail', ride_id=ride_id))

    pickup = pickup_point or ride['Source']
    dropoff = dropoff_point or ride['Destination']
    fare_total = agreed_fare if agreed_fare > 0 else float(ride['Fare_Per_Seat']) * seats_requested

    req_id, _ = execute_update("""
        INSERT INTO RIDE_REQUEST (User_ID, Ride_ID, Pickup_Point, Dropoff_Point, Seats_Requested, Agreed_Fare, Request_Status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
    """, (user['User_ID'], ride_id, pickup, dropoff, seats_requested, fare_total))

    execute_update("""
        INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
        VALUES (%s, 'Ride_Request', %s, 0)
    """, (ride['Driver_ID'], f"{user['Name']} wants to split your cab ({pickup} -> {dropoff}) for {seats_requested} seat(s)."))

    if req_id:
        sync_request_to_cloud(req_id)
    sync_ride_to_cloud(ride_id)

    sync_to_firebase('live_events', {
        'event': 'request_created',
        'ride_id': ride_id,
        'request_id': req_id,
        'user_id': user['User_ID'],
        'user_name': user['Name'],
        'driver_id': ride['Driver_ID'],
        'timestamp': int(time.time())
    })

    flash(f"Cab-share request sent to host! Awaiting approval.", "success")
    return redirect(url_for('ride_detail', ride_id=ride_id))

@app.route('/requests')
@login_required
def requests_management():
    sync_all_cloud_requests()
    user = get_current_user()
    
    incoming_requests = execute_query("""
        SELECT rr.*, p.Name as Passenger_Name, p.Phone_Number as Passenger_Phone, p.Profile_Picture as Passenger_Avatar, p.Gender as Passenger_Gender,
               r.Source, r.Destination, r.Date, r.Time, r.Fare_Per_Seat, r.Available_Seats, r.Ride_Type, r.Is_Women_Only, r.Ride_Status,
               (SELECT COUNT(*) FROM RATING_REVIEW rv WHERE rv.Request_ID = rr.Request_ID AND rv.Reviewer_ID = %s) as Has_Reviewed
        FROM RIDE_REQUEST rr
        JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
        JOIN USER p ON rr.User_ID = p.User_ID
        WHERE r.Driver_ID = %s
        ORDER BY rr.Request_Time DESC
    """, (user['User_ID'], user['User_ID']))

    my_requests = execute_query("""
        SELECT rr.*, d.Name as Driver_Name, d.Phone_Number as Driver_Phone, d.Profile_Picture as Driver_Avatar, d.Average_Rating as Driver_Rating,
               r.Source, r.Destination, r.Date, r.Time, r.Fare_Per_Seat, r.Ride_Type, r.Ride_Status,
               (SELECT COUNT(*) FROM RATING_REVIEW rv WHERE rv.Request_ID = rr.Request_ID AND rv.Reviewer_ID = %s) as Has_Reviewed
        FROM RIDE_REQUEST rr
        JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
        JOIN USER d ON r.Driver_ID = d.User_ID
        WHERE rr.User_ID = %s
        ORDER BY rr.Request_Time DESC
    """, (user['User_ID'], user['User_ID']))

    return render_template('requests.html', incoming=incoming_requests, my_requests=my_requests)

@app.route('/requests/<int:request_id>/respond', methods=['POST'])
@login_required
def respond_request(request_id):
    sync_all_cloud_requests()
    user = get_current_user()
    decision = request.form.get('decision')

    req = execute_query("""
        SELECT rr.*, r.Driver_ID, r.Available_Seats, r.Source, r.Destination, r.Estimated_Distance_Km, p.Name as Passenger_Name
        FROM RIDE_REQUEST rr
        JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
        JOIN USER p ON rr.User_ID = p.User_ID
        WHERE rr.Request_ID = %s
    """, (request_id,), fetchone=True)

    if not req:
        req = restore_request_from_cloud(request_id)

    if not req or req['Driver_ID'] != user['User_ID']:
        flash("Unauthorized.", "danger")
        return redirect(url_for('requests_management'))

    if decision == 'Accepted':
        restore_ride_from_cloud(req['Ride_ID'])
        current_ride = execute_query("SELECT Available_Seats FROM RIDE WHERE Ride_ID = %s", (req['Ride_ID'],), fetchone=True)
        avail = current_ride['Available_Seats'] if current_ride else 0

        if req['Seats_Requested'] > avail:
            flash(f"Cannot accept: Only {avail} seat(s) remaining.", "danger")
            return redirect(url_for('requests_management'))

        # Accept the request. The MySQL trigger

        # Accept the request. The MySQL trigger
        # trg_after_ride_request_status_update handles the seat deduction
        # when Request_Status changes from Pending to Accepted.
        execute_update(
            "UPDATE RIDE_REQUEST SET Request_Status = 'Accepted' WHERE Request_ID = %s",
            (request_id,)
        )

        updated_ride = execute_query("SELECT Available_Seats FROM RIDE WHERE Ride_ID = %s", (req['Ride_ID'],), fetchone=True)
        rem_seats = updated_ride['Available_Seats'] if updated_ride else 0

        if rem_seats <= 0:
            execute_update("""
                UPDATE RIDE_REQUEST SET Request_Status = 'Cancelled' 
                WHERE Ride_ID = %s AND Request_Status = 'Pending'
            """, (req['Ride_ID'],))

        sync_request_to_cloud(request_id)
        sync_ride_to_cloud(req['Ride_ID'])
        
        # Financial & Carbon Savings Calculation
        saved_amt = float(req['Agreed_Fare']) * 1.5 if float(req['Agreed_Fare']) > 0 else 200.0
        co2_saved = round(0.14 * float(req.get('Estimated_Distance_Km') or 25.0) * int(req['Seats_Requested']), 2)
        
        # Update Passenger
        execute_update("""
            UPDATE USER 
            SET Total_Money_Saved = Total_Money_Saved + %s,
                CO2_Saved_Kg = CO2_Saved_Kg + %s
            WHERE User_ID = %s
        """, (saved_amt, co2_saved, req['User_ID']))

        # Update Host (Eco and Money Saved)
        execute_update("""
            UPDATE USER 
            SET Total_Money_Saved = Total_Money_Saved + %s,
                CO2_Saved_Kg = CO2_Saved_Kg + %s
            WHERE User_ID = %s
        """, (saved_amt * 0.8, co2_saved, req['Driver_ID']))

        execute_update("""
            INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
            VALUES (%s, 'Request_Accepted', %s, 0)
        """, (req['User_ID'], f"Cab Share Confirmed! Your request for {req['Pickup_Point'] or req['Source']} to {req['Dropoff_Point'] or req['Destination']} was ACCEPTED. You prevented {co2_saved} kg of CO2 emissions!"))

        flash(f"Accepted {req['Passenger_Name']}! Available seats updated automatically.", "success")
    elif decision == 'Rejected':
        execute_update("UPDATE RIDE_REQUEST SET Request_Status = 'Rejected' WHERE Request_ID = %s", (request_id,))
        sync_request_to_cloud(request_id)
        execute_update("""
            INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
            VALUES (%s, 'Request_Rejected', %s, 0)
        """, (req['User_ID'], "Your cab-share request was declined."))
        flash("Request rejected.", "info")

    sync_to_firebase('live_events', {
        'event': 'request_responded',
        'request_id': request_id,
        'ride_id': req['Ride_ID'],
        'decision': decision,
        'passenger_id': req['User_ID'],
        'driver_id': req['Driver_ID'],
        'timestamp': int(time.time())
    })

    return redirect(url_for('requests_management'))

# ============================================================================
# 7. 5-STAR RATINGS & REVIEWS (TRIGGER IMPLEMENTATION)
# ============================================================================
@app.route('/reviews/add/<int:request_id>', methods=['POST'])
@login_required
def add_review(request_id):
    user = get_current_user()
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '').strip()

    req = execute_query("""
        SELECT rr.*, r.Driver_ID
        FROM RIDE_REQUEST rr
        JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
        WHERE rr.Request_ID = %s
    """, (request_id,), fetchone=True)

    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for('requests_management'))

    # Determine Reviewee
    if user['User_ID'] == req['User_ID']:
        reviewee_id = req['Driver_ID']
    elif user['User_ID'] == req['Driver_ID']:
        reviewee_id = req['User_ID']
    else:
        flash("Unauthorized.", "danger")
        return redirect(url_for('requests_management'))

    # Check for existing review
    existing = execute_query("""
        SELECT Review_ID FROM RATING_REVIEW 
        WHERE Request_ID = %s AND Reviewer_ID = %s
    """, (request_id, user['User_ID']), fetchone=True)

    if existing:
        flash("You have already reviewed this trip.", "info")
        return redirect(url_for('requests_management'))

    # Insert Review
    execute_update("""
        INSERT INTO RATING_REVIEW (Request_ID, Reviewer_ID, Reviewee_ID, Rating, Comment)
        VALUES (%s, %s, %s, %s, %s)
    """, (request_id, user['User_ID'], reviewee_id, rating, comment))

    # Recalculate Average Rating for Reviewee (DB Trigger Logic)
    agg = execute_query("""
        SELECT AVG(Rating) as avg_r, COUNT(*) as cnt
        FROM RATING_REVIEW
        WHERE Reviewee_ID = %s
    """, (reviewee_id,), fetchone=True)

    new_avg = round(float(agg['avg_r']), 2) if agg and agg['avg_r'] else 5.0
    new_cnt = agg['cnt'] if agg else 1

    execute_update("""
        UPDATE USER 
        SET Average_Rating = %s, Total_Reviews = %s
        WHERE User_ID = %s
    """, (new_avg, new_cnt, reviewee_id))

    execute_update("""
        INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
        VALUES (%s, 'General', %s, 0)
    """, (reviewee_id, f"⭐ {user['Name']} left you a {rating}-star review: '{comment or 'Great ride!'}'"))

    flash(f"Thank you! Your {rating}-star rating was submitted.", "success")
    next_url = request.form.get('next') or request.referrer or url_for('requests_management')
    return redirect(next_url)

# ============================================================================
# 8. COMMUTE PASSES & AUTO-ASSIGNMENT (WEEKLY & MONTHLY)
# ============================================================================
@app.route('/passes', methods=['GET', 'POST'])
@login_required
def passes_view():
    user = get_current_user()

    if request.method == 'POST':
        host_id = int(request.form.get('host_id'))
        source = request.form.get('source', '').strip()
        destination = request.form.get('destination', '').strip()
        pass_type = request.form.get('pass_type', 'Weekly')

        start_date = datetime.now().date()
        if pass_type == 'Weekly':
            end_date = start_date + timedelta(days=7)
            price = 800.00
            discount = 20
        else:
            end_date = start_date + timedelta(days=30)
            price = 2800.00
            discount = 35

        execute_update("""
            INSERT INTO COMMUTE_PASS (Passenger_ID, Host_ID, Source, Destination, Pass_Type, Start_Date, End_Date, Total_Price, Discount_Pct, Pass_Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (user['User_ID'], host_id, source, destination, pass_type, start_date, end_date, price, discount))

        execute_update("""
            INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
            VALUES (%s, 'General', %s, 0)
        """, (host_id, f"🎫 New Pass Subscriber! {user['Name']} bought a {pass_type} Pass for your {source} -> {destination} corridor."))

        flash(f"🎉 {pass_type} Pass activated! You will now be automatically assigned a seat on all future rides by this host.", "success")
        return redirect(url_for('passes_view'))

    active_passes = execute_query("""
        SELECT cp.*, h.Name as Host_Name, h.Profile_Picture as Host_Avatar, h.Phone_Number as Host_Phone
        FROM COMMUTE_PASS cp
        JOIN USER h ON cp.Host_ID = h.User_ID
        WHERE cp.Passenger_ID = %s AND cp.Pass_Status = 'Active'
        ORDER BY cp.Created_At DESC
    """, (user['User_ID'],))

    available_hosts = execute_query("""
        SELECT User_ID, Name, Phone_Number, Profile_Picture, Average_Rating
        FROM USER
        WHERE User_ID != %s
        ORDER BY Average_Rating DESC
    """, (user['User_ID'],))

    return render_template('passes.html', active_passes=active_passes, available_hosts=available_hosts)

# ============================================================================
# 9. CHAT & SOCIAL (RULES #7 & #5)
# ============================================================================
@app.route('/chat/<int:request_id>', methods=['GET', 'POST'])
@login_required
def chat_view(request_id):
    sync_all_cloud_requests()
    user = get_current_user()

    req_info = execute_query("""
        SELECT rr.*, r.Driver_ID, r.Source, r.Destination, r.Date,
               p.User_ID as Passenger_ID, p.Name as Passenger_Name, p.Profile_Picture as Passenger_Avatar,
               d.User_ID as Driver_ID, d.Name as Driver_Name, d.Profile_Picture as Driver_Avatar
        FROM RIDE_REQUEST rr
        JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
        JOIN USER p ON rr.User_ID = p.User_ID
        JOIN USER d ON r.Driver_ID = d.User_ID
        WHERE rr.Request_ID = %s
    """, (request_id,), fetchone=True)

    if not req_info:
        restored = restore_request_from_cloud(request_id)
        if restored:
            req_info = execute_query("""
                SELECT rr.*, r.Driver_ID, r.Source, r.Destination, r.Date,
                       p.User_ID as Passenger_ID, p.Name as Passenger_Name, p.Profile_Picture as Passenger_Avatar,
                       d.User_ID as Driver_ID, d.Name as Driver_Name, d.Profile_Picture as Driver_Avatar
                FROM RIDE_REQUEST rr
                JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
                JOIN USER p ON rr.User_ID = p.User_ID
                JOIN USER d ON r.Driver_ID = d.User_ID
                WHERE rr.Request_ID = %s
            """, (request_id,), fetchone=True)

    if not req_info:
        flash("Booking request not found.", "danger")
        return redirect(url_for('requests_management'))

    if req_info['Request_Status'] != 'Accepted':
        flash("Chat is only allowed after the ride request has been ACCEPTED (Business Rule #7).", "warning")
        return redirect(url_for('requests_management'))

    other_user = {
        'id': req_info['Driver_ID'] if user['User_ID'] == req_info['Passenger_ID'] else req_info['Passenger_ID'],
        'name': req_info['Driver_Name'] if user['User_ID'] == req_info['Passenger_ID'] else req_info['Passenger_Name'],
        'avatar': req_info['Driver_Avatar'] if user['User_ID'] == req_info['Passenger_ID'] else req_info['Passenger_Avatar']
    }

    restore_chats_from_cloud(request_id=request_id)

    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg:
            chat_id, _ = execute_update("""
                INSERT INTO CHAT (Request_ID, Sender_ID, Receiver_ID, Message, Seen_Status)
                VALUES (%s, %s, %s, %s, 'Unread')
            """, (request_id, user['User_ID'], other_user['id'], msg))

            sync_chat_msg_to_cloud(chat_id, request_id, user['User_ID'], other_user['id'], msg, datetime.now(), 'Unread')

            sync_to_firebase('live_events', {
                'event': 'ride_message',
                'request_id': request_id,
                'sender_id': user['User_ID'],
                'receiver_id': other_user['id'],
                'timestamp': int(time.time())
            })
            return redirect(url_for('chat_view', request_id=request_id))

    messages = execute_query("""
        SELECT c.*, s.Name as Sender_Name, s.Profile_Picture as Sender_Avatar
        FROM CHAT c
        JOIN USER s ON c.Sender_ID = s.User_ID
        WHERE c.Request_ID = %s
        ORDER BY c.Sent_Time ASC
    """, (request_id,))

    execute_update("UPDATE CHAT SET Seen_Status = 'Read' WHERE Request_ID = %s AND Receiver_ID = %s", (request_id, user['User_ID']))

    return render_template('chat.html', req_info=req_info, other_user=other_user, messages=messages)

@app.route('/friends', methods=['GET', 'POST'])
@login_required
def friends_view():
    user = get_current_user()

    if request.method == 'POST':
        receiver_id = int(request.form.get('receiver_id'))
        if receiver_id != user['User_ID']:
            try:
                execute_update("""
                    INSERT INTO FRIEND (Sender_ID, Receiver_ID, Friend_Status)
                    VALUES (%s, %s, 'Pending')
                """, (user['User_ID'], receiver_id))
                execute_update("""
                    INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read)
                    VALUES (%s, 'Friend_Request', %s, 0)
                """, (receiver_id, f"{user['Name']} sent you a friend request."))
                flash("Friend request sent!", "success")
            except Exception as e:
                flash(f"Could not send request: {e}", "danger")
        return redirect(url_for('friends_view'))

    friends = execute_query("""
        SELECT f.Friend_ID, f.Request_Date,
               CASE WHEN f.Sender_ID = %s THEN u2.User_ID ELSE u1.User_ID END as Friend_User_ID,
               CASE WHEN f.Sender_ID = %s THEN u2.Name ELSE u1.Name END as Friend_Name,
               CASE WHEN f.Sender_ID = %s THEN u2.Phone_Number ELSE u1.Phone_Number END as Friend_Phone,
               CASE WHEN f.Sender_ID = %s THEN u2.Profile_Picture ELSE u1.Profile_Picture END as Friend_Avatar
        FROM FRIEND f
        JOIN USER u1 ON f.Sender_ID = u1.User_ID
        JOIN USER u2 ON f.Receiver_ID = u2.User_ID
        WHERE (f.Sender_ID = %s OR f.Receiver_ID = %s) AND f.Friend_Status = 'Accepted'
    """, (user['User_ID'], user['User_ID'], user['User_ID'], user['User_ID'], user['User_ID'], user['User_ID']))

    pending_received = execute_query("""
        SELECT f.Friend_ID, f.Request_Date, u.User_ID as Sender_ID, u.Name as Sender_Name, u.Profile_Picture as Sender_Avatar
        FROM FRIEND f
        JOIN USER u ON f.Sender_ID = u.User_ID
        WHERE f.Receiver_ID = %s AND f.Friend_Status = 'Pending'
    """, (user['User_ID'],))

    potential_friends = execute_query("""
        SELECT User_ID, Name, Phone_Number, Profile_Picture
        FROM USER
        WHERE User_ID != %s
          AND User_ID NOT IN (
              SELECT Receiver_ID FROM FRIEND WHERE Sender_ID = %s
              UNION
              SELECT Sender_ID FROM FRIEND WHERE Receiver_ID = %s
          )
    """, (user['User_ID'], user['User_ID'], user['User_ID']))

    return render_template('friends.html', friends=friends, pending_received=pending_received, potential_friends=potential_friends)

@app.route('/friends/<int:friend_id>/accept', methods=['POST'])
@login_required
def accept_friend(friend_id):
    user = get_current_user()
    execute_update("UPDATE FRIEND SET Friend_Status = 'Accepted' WHERE Friend_ID = %s AND Receiver_ID = %s", (friend_id, user['User_ID']))
    flash("Friend request accepted!", "success")
    return redirect(url_for('friends_view'))

@app.route('/friends/chat/<int:friend_user_id>', methods=['GET', 'POST'])
@login_required
def friend_chat_view(friend_user_id):
    user = get_current_user()
    ensure_user_in_sqlite(user)

    friend_user = execute_query("SELECT User_ID, Name, Phone_Number, Profile_Picture, Gender, Average_Rating FROM USER WHERE User_ID = %s", (friend_user_id,), fetchone=True)
    if not friend_user:
        fb_u = get_from_firebase(f"users/{friend_user_id}") or {}
        friend_user = {
            'User_ID': friend_user_id,
            'Name': fb_u.get('name', f'Co-Commuter #{friend_user_id}'),
            'Phone_Number': fb_u.get('phone', '9876543210'),
            'Profile_Picture': fb_u.get('avatar', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150'),
            'Gender': fb_u.get('gender', 'Other'),
            'Average_Rating': 5.0
        }
        ensure_user_in_sqlite(friend_user)

    chat_key = f"{min(user['User_ID'], friend_user_id)}_{max(user['User_ID'], friend_user_id)}"

    restore_chats_from_cloud(chat_key=chat_key)

    if request.method == 'POST':
        message_text = request.form.get('message', '').strip()
        if message_text:
            chat_id, _ = execute_update("""
                INSERT INTO CHAT (Sender_ID, Receiver_ID, Message, Seen_Status)
                VALUES (%s, %s, %s, 'Unread')
            """, (user['User_ID'], friend_user_id, message_text))

            sync_chat_msg_to_cloud(chat_id, None, user['User_ID'], friend_user_id, message_text, datetime.now(), 'Unread', chat_key=chat_key)

            sync_to_firebase('live_events', {
                'event': 'friend_message',
                'chat_key': chat_key,
                'sender_id': user['User_ID'],
                'receiver_id': friend_user_id,
                'timestamp': int(time.time())
            })
            flash("Message sent!", "success")
        return redirect(url_for('friend_chat_view', friend_user_id=friend_user_id))

    messages = execute_query("""
        SELECT c.*, u.Name as Sender_Name, u.Profile_Picture as Sender_Avatar
        FROM CHAT c
        JOIN USER u ON c.Sender_ID = u.User_ID
        WHERE (c.Sender_ID = %s AND c.Receiver_ID = %s)
           OR (c.Sender_ID = %s AND c.Receiver_ID = %s)
        ORDER BY c.Sent_Time ASC
    """, (user['User_ID'], friend_user_id, friend_user_id, user['User_ID']))

    execute_update("UPDATE CHAT SET Seen_Status = 'Read' WHERE Sender_ID = %s AND Receiver_ID = %s", (friend_user_id, user['User_ID']))

    return render_template('friend_chat.html', friend_user=friend_user, messages=messages, chat_key=chat_key)

@app.route('/notifications')
@login_required
def notifications_view():
    user = get_current_user()
    notifications = execute_query(
        "SELECT * FROM NOTIFICATION WHERE User_ID = %s ORDER BY Created_At DESC",
        (user['User_ID'],)
    )
    execute_update("UPDATE NOTIFICATION SET Is_Read = 1 WHERE User_ID = %s", (user['User_ID'],))
    return render_template('notifications.html', notifications=notifications)

# ============================================================================
# 10. SQL CONSOLE
# ============================================================================
@app.route('/sql-console', methods=['GET', 'POST'])
def sql_console():
    query_result = None
    error_msg = None
    executed_sql = request.form.get('sql_query', '').strip() if request.method == 'POST' else ''
    affected_rows = None

    preloaded_queries = [
        ("View Commuter Passes & Auto-Assigns", "SELECT cp.Pass_ID, p.Name as Commuter, h.Name as Host, cp.Source, cp.Destination, cp.Pass_Type, cp.Pass_Status FROM COMMUTE_PASS cp JOIN USER p ON cp.Passenger_ID = p.User_ID JOIN USER h ON cp.Host_ID = h.User_ID;"),
        ("View Ratings & Reviews Breakdown", "SELECT rv.Review_ID, u1.Name as Reviewer, u2.Name as Host, rv.Rating, rv.Comment FROM RATING_REVIEW rv JOIN USER u1 ON rv.Reviewer_ID = u1.User_ID JOIN USER u2 ON rv.Reviewee_ID = u2.User_ID;"),
        ("All Tables Row Counts Overview", "SELECT 'USER' as Table_Name, COUNT(*) as Total_Records FROM USER UNION SELECT 'RIDE', COUNT(*) FROM RIDE UNION SELECT 'STOP', COUNT(*) FROM STOP UNION SELECT 'RIDE_REQUEST', COUNT(*) FROM RIDE_REQUEST UNION SELECT 'COMMUTE_PASS', COUNT(*) FROM COMMUTE_PASS UNION SELECT 'RATING_REVIEW', COUNT(*) FROM RATING_REVIEW UNION SELECT 'CHAT', COUNT(*) FROM CHAT UNION SELECT 'NOTIFICATION', COUNT(*) FROM NOTIFICATION UNION SELECT 'FRIEND', COUNT(*) FROM FRIEND;")
    ]

    if request.method == 'POST' and executed_sql:
        try:
            if executed_sql.lower().startswith(('select', 'show', 'describe', 'explain', 'pragma')):
                query_result = execute_query(executed_sql)
            else:
                last_id, rowcount = execute_update(executed_sql)
                affected_rows = f"Command executed successfully. Affected Rows: {rowcount}, Last Insert ID: {last_id}"
        except Exception as e:
            error_msg = str(e)

    table_stats = []
    tables = ['USER', 'RIDE', 'STOP', 'RIDE_REQUEST', 'COMMUTE_PASS', 'RATING_REVIEW', 'CHAT', 'NOTIFICATION', 'FRIEND']
    for t in tables:
        try:
            cnt = execute_query(f"SELECT COUNT(*) as count FROM {t}", fetchone=True)['count']
            table_stats.append({'name': t, 'count': cnt})
        except:
            pass

    return render_template('sql_console.html',
                           executed_sql=executed_sql,
                           query_result=query_result,
                           affected_rows=affected_rows,
                           error_msg=error_msg,
                           preloaded_queries=preloaded_queries,
                           table_stats=table_stats)

@app.errorhandler(500)
def internal_server_error(e):
    print(f"[ERROR 500] {e}")
    try:
        if get_active_engine() == 'sqlite':
            _init_sqlite_db(force_reinit=False)
    except Exception as ex:
        print(f"[WARN] Failed to reinit DB on 500: {ex}")
    flash("A temporary server glitch occurred. Automatically recovered database!", "warning")
    return redirect(request.referrer or url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    flash("The requested page or route was not found.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("================================================================")
    print(" [*] CabShare Passes, Reviews & DBMS Server Starting...")
    print(" [*] Access the application at: http://127.0.0.1:5000")
    print("================================================================")
    app.run(debug=True, host='127.0.0.1', port=5000)
