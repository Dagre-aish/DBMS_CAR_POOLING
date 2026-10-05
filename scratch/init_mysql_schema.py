import pymysql

host = 'localhost'
port = 3306
user = 'root'
password = 'root'

print("[1] Connecting to MySQL...")
conn = pymysql.connect(host=host, port=port, user=user, password=password, autocommit=True)
cursor = conn.cursor()

print("[2] Creating database carpooling_db...")
cursor.execute("DROP DATABASE IF EXISTS carpooling_db;")
cursor.execute("CREATE DATABASE carpooling_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
cursor.execute("USE carpooling_db;")

schema_queries = [
    """
    CREATE TABLE USER (
        User_ID INT AUTO_INCREMENT PRIMARY KEY,
        Name VARCHAR(100) NOT NULL,
        Phone_Number VARCHAR(20) NOT NULL UNIQUE,
        Password VARCHAR(255) NOT NULL,
        Email VARCHAR(150) NULL,
        Gender ENUM('Male', 'Female', 'Other') NOT NULL DEFAULT 'Other',
        Profile_Picture VARCHAR(255) DEFAULT 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
        Total_Money_Saved DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
        Average_Rating DECIMAL(3, 2) NOT NULL DEFAULT 5.00,
        Total_Reviews INT NOT NULL DEFAULT 0,
        CO2_Saved_Kg DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT chk_user_phone CHECK (LENGTH(Phone_Number) >= 8)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE RIDE (
        Ride_ID INT AUTO_INCREMENT PRIMARY KEY,
        Driver_ID INT NOT NULL,
        Source VARCHAR(150) NOT NULL,
        Destination VARCHAR(150) NOT NULL,
        Date DATE NOT NULL,
        Time TIME NOT NULL,
        Total_Seats INT NOT NULL,
        Available_Seats INT NOT NULL,
        Fare_Per_Seat DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
        Total_Cab_Fare DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
        Ride_Type ENUM('Cab_Share', 'Carpool', 'Auto_Share') NOT NULL DEFAULT 'Cab_Share',
        Vehicle_Info VARCHAR(100) NOT NULL DEFAULT 'Uber / Ola Cab',
        Is_Women_Only BOOLEAN NOT NULL DEFAULT 0,
        Estimated_Distance_Km DECIMAL(6, 2) NOT NULL DEFAULT 25.00,
        Ride_Status ENUM('Scheduled', 'Ongoing', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Scheduled',
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_ride_driver FOREIGN KEY (Driver_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT chk_total_seats CHECK (Total_Seats > 0),
        CONSTRAINT chk_available_seats CHECK (Available_Seats >= 0 AND Available_Seats <= Total_Seats),
        CONSTRAINT chk_fare_positive CHECK (Fare_Per_Seat >= 0.00)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE STOP (
        Stop_ID INT AUTO_INCREMENT PRIMARY KEY,
        Ride_ID INT NOT NULL,
        Stop_Name VARCHAR(150) NOT NULL,
        Stop_Order INT NOT NULL,
        Arrival_Time TIME NULL,
        Estimated_Sub_Fare DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
        Latitude DECIMAL(10, 6) NULL,
        Longitude DECIMAL(10, 6) NULL,
        CONSTRAINT fk_stop_ride FOREIGN KEY (Ride_ID) REFERENCES RIDE(Ride_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT uq_ride_stop_order UNIQUE (Ride_ID, Stop_Order),
        CONSTRAINT chk_stop_order CHECK (Stop_Order >= 1)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE RIDE_REQUEST (
        Request_ID INT AUTO_INCREMENT PRIMARY KEY,
        User_ID INT NOT NULL,
        Ride_ID INT NOT NULL,
        Pickup_Point VARCHAR(150) NULL,
        Dropoff_Point VARCHAR(150) NULL,
        Seats_Requested INT NOT NULL DEFAULT 1,
        Agreed_Fare DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
        Request_Status ENUM('Pending', 'Accepted', 'Rejected', 'Cancelled') NOT NULL DEFAULT 'Pending',
        Request_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_request_user FOREIGN KEY (User_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_request_ride FOREIGN KEY (Ride_ID) REFERENCES RIDE(Ride_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT chk_seats_req CHECK (Seats_Requested > 0)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE CHAT (
        Chat_ID INT AUTO_INCREMENT PRIMARY KEY,
        Request_ID INT NULL DEFAULT NULL,
        Sender_ID INT NOT NULL,
        Receiver_ID INT NOT NULL,
        Message TEXT NOT NULL,
        Sent_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Seen_Status ENUM('Unread', 'Read') NOT NULL DEFAULT 'Unread',
        CONSTRAINT fk_chat_request FOREIGN KEY (Request_ID) REFERENCES RIDE_REQUEST(Request_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_chat_sender FOREIGN KEY (Sender_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_chat_receiver FOREIGN KEY (Receiver_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE NOTIFICATION (
        Notification_ID INT AUTO_INCREMENT PRIMARY KEY,
        User_ID INT NOT NULL,
        Notification_Type ENUM('Ride_Request', 'Request_Accepted', 'Request_Rejected', 'Ride_Cancelled', 'New_Message', 'Friend_Request', 'General') NOT NULL DEFAULT 'General',
        Message VARCHAR(255) NOT NULL,
        Is_Read BOOLEAN NOT NULL DEFAULT FALSE,
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_notification_user FOREIGN KEY (User_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE FRIEND (
        Friend_ID INT AUTO_INCREMENT PRIMARY KEY,
        Sender_ID INT NOT NULL,
        Receiver_ID INT NOT NULL,
        Friend_Status ENUM('Pending', 'Accepted', 'Blocked') NOT NULL DEFAULT 'Pending',
        Request_Date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_friend_sender FOREIGN KEY (Sender_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_friend_receiver FOREIGN KEY (Receiver_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT uq_friend_pair UNIQUE (Sender_ID, Receiver_ID)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE RATING_REVIEW (
        Review_ID INT AUTO_INCREMENT PRIMARY KEY,
        Request_ID INT NOT NULL,
        Reviewer_ID INT NOT NULL,
        Reviewee_ID INT NOT NULL,
        Rating INT NOT NULL,
        Comment TEXT NULL,
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_review_request FOREIGN KEY (Request_ID) REFERENCES RIDE_REQUEST(Request_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_review_reviewer FOREIGN KEY (Reviewer_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_review_reviewee FOREIGN KEY (Reviewee_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT chk_review_rating CHECK (Rating >= 1 AND Rating <= 5)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE COMMUTE_PASS (
        Pass_ID INT AUTO_INCREMENT PRIMARY KEY,
        Passenger_ID INT NOT NULL,
        Host_ID INT NOT NULL,
        Source VARCHAR(150) NOT NULL,
        Destination VARCHAR(150) NOT NULL,
        Pass_Type ENUM('Weekly', 'Monthly') NOT NULL DEFAULT 'Weekly',
        Start_Date DATE NOT NULL,
        End_Date DATE NOT NULL,
        Total_Price DECIMAL(10, 2) NOT NULL,
        Discount_Pct INT NOT NULL DEFAULT 20,
        Pass_Status ENUM('Active', 'Expired', 'Cancelled') NOT NULL DEFAULT 'Active',
        Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_pass_passenger FOREIGN KEY (Passenger_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_pass_host FOREIGN KEY (Host_ID) REFERENCES USER(User_ID) ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB;
    """
]

print("[3] Creating MySQL Tables...")
for q in schema_queries:
    cursor.execute(q)

seed_queries = [
    """
    INSERT INTO USER (User_ID, Name, Phone_Number, Password, Email, Gender, Profile_Picture, Total_Money_Saved, Average_Rating, Total_Reviews, CO2_Saved_Kg) VALUES
    (1, 'Aishwarya D.', '9876543210', 'pass123', 'aishwarya@example.com', 'Female', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150', 1250.00, 4.95, 12, 45.20),
    (2, 'Rahul Sharma', '9876543211', 'pass123', 'rahul@example.com', 'Male', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 840.00, 4.80, 8, 28.50),
    (3, 'Priya Patel', '9876543212', 'pass123', 'priya@example.com', 'Female', 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150', 1600.00, 5.00, 15, 62.00),
    (4, 'Vikram Malhotra', '9876543213', 'pass123', 'vikram@example.com', 'Male', 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150', 450.00, 4.70, 5, 18.00),
    (5, 'Neha Gupta', '9876543214', 'pass123', 'neha@example.com', 'Female', 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150', 920.00, 4.90, 10, 34.00);
    """,
    """
    INSERT INTO RIDE (Ride_ID, Driver_ID, Source, Destination, Date, Time, Total_Seats, Available_Seats, Fare_Per_Seat, Total_Cab_Fare, Ride_Type, Vehicle_Info, Is_Women_Only, Estimated_Distance_Km, Ride_Status) VALUES
    (1, 1, 'Thane', 'BKC', '2026-10-10', '08:30:00', 3, 2, 120.00, 480.00, 'Cab_Share', 'Uber XL', 1, 28.0, 'Scheduled'),
    (2, 2, 'Dadar', 'Hinjewadi', '2026-10-11', '09:00:00', 3, 3, 350.00, 1400.00, 'Cab_Share', 'Ola Prime Sedan', 0, 140.0, 'Scheduled'),
    (3, 3, 'Koramangala', 'Whitefield', '2026-10-10', '08:45:00', 3, 1, 180.00, 720.00, 'Cab_Share', 'Uber Black', 0, 22.0, 'Scheduled');
    """,
    """
    INSERT INTO STOP (Stop_ID, Ride_ID, Stop_Name, Stop_Order, Arrival_Time, Estimated_Sub_Fare, Latitude, Longitude) VALUES
    (1, 1, 'Mulund Check Naka', 1, '08:45:00', 40.00, 19.1764, 72.9567),
    (2, 1, 'Ghatkopar East (EEH)', 2, '09:05:00', 80.00, 19.0860, 72.9090),
    (3, 3, 'Marathahalli Bridge', 1, '09:15:00', 100.00, 12.9591, 77.6974);
    """,
    """
    INSERT INTO RIDE_REQUEST (Request_ID, User_ID, Ride_ID, Pickup_Point, Dropoff_Point, Seats_Requested, Agreed_Fare, Request_Status) VALUES
    (1, 2, 1, 'Thane', 'BKC', 1, 120.00, 'Accepted'),
    (2, 4, 3, 'Koramangala', 'Whitefield', 2, 360.00, 'Accepted');
    """,
    """
    INSERT INTO FRIEND (Friend_ID, Sender_ID, Receiver_ID, Friend_Status) VALUES
    (1, 1, 2, 'Accepted'),
    (2, 1, 3, 'Accepted'),
    (3, 2, 4, 'Accepted');
    """
]

print("[4] Inserting Sample Seed Data...")
for q in seed_queries:
    cursor.execute(q)

cursor.execute("SHOW TABLES;")
tables = cursor.fetchall()
print("\n[SUCCESS] Local MySQL Database 'carpooling_db' successfully created and seeded!")
print("Tables:", [t[0] for t in tables])

conn.close()
