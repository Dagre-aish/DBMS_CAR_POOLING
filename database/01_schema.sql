-- ============================================================================
-- DATABASE MANAGEMENT SYSTEMS PROJECT: COMMUTER CAB-SHARING & CARPOOLING
-- Script 01: Database Creation & Table Schema (DDL)
-- Features: Cab-Share, Multi-Waypoints, Women-Only, Ratings, CO2 Tracker, Commute Passes
-- ============================================================================

CREATE DATABASE IF NOT EXISTS carpooling_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE carpooling_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS COMMUTE_PASS;
DROP TABLE IF EXISTS RATING_REVIEW;
DROP TABLE IF EXISTS CHAT;
DROP TABLE IF EXISTS NOTIFICATION;
DROP TABLE IF EXISTS FRIEND;
DROP TABLE IF EXISTS RIDE_REQUEST;
DROP TABLE IF EXISTS STOP;
DROP TABLE IF EXISTS RIDE;
DROP TABLE IF EXISTS USER;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 1. USER TABLE (Commuters seeking to share rides & split cab fares)
-- ============================================================================
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

-- ============================================================================
-- 2. RIDE TABLE (Cab-Share / Commute Pool offering)
-- Includes Total Cab Fare for fair splitting, Women-Only mode, and Trip Distance
-- ============================================================================
CREATE TABLE RIDE (
    Ride_ID INT AUTO_INCREMENT PRIMARY KEY,
    Driver_ID INT NOT NULL,  -- Commuter who booked/hosts the cab or vehicle
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
    
    CONSTRAINT fk_ride_driver 
        FOREIGN KEY (Driver_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT chk_total_seats CHECK (Total_Seats > 0),
    CONSTRAINT chk_available_seats CHECK (Available_Seats >= 0 AND Available_Seats <= Total_Seats),
    CONSTRAINT chk_fare_positive CHECK (Fare_Per_Seat >= 0.00)
) ENGINE=InnoDB;

-- ============================================================================
-- 3. STOP TABLE (Multiple Intermediate Pickup / Drop Waypoints)
-- Supports ordered waypoints, estimated arrival times, and sub-segment fares
-- ============================================================================
CREATE TABLE STOP (
    Stop_ID INT AUTO_INCREMENT PRIMARY KEY,
    Ride_ID INT NOT NULL,
    Stop_Name VARCHAR(150) NOT NULL,
    Stop_Order INT NOT NULL,
    Arrival_Time TIME NULL,
    Estimated_Sub_Fare DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    Latitude DECIMAL(10, 6) NULL,
    Longitude DECIMAL(10, 6) NULL,
    
    CONSTRAINT fk_stop_ride 
        FOREIGN KEY (Ride_ID) REFERENCES RIDE(Ride_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT uq_ride_stop_order UNIQUE (Ride_ID, Stop_Order),
    CONSTRAINT chk_stop_order CHECK (Stop_Order >= 1)
) ENGINE=InnoDB;

-- ============================================================================
-- 4. RIDE_REQUEST TABLE (Booking / Fare Split Request)
-- ============================================================================
CREATE TABLE RIDE_REQUEST (
    Request_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT NOT NULL,  -- Co-commuter requesting to share cab
    Ride_ID INT NOT NULL,
    Pickup_Point VARCHAR(150) NULL,
    Dropoff_Point VARCHAR(150) NULL,
    Seats_Requested INT NOT NULL DEFAULT 1,
    Agreed_Fare DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    Request_Status ENUM('Pending', 'Accepted', 'Rejected', 'Cancelled') NOT NULL DEFAULT 'Pending',
    Request_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_request_user 
        FOREIGN KEY (User_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_request_ride 
        FOREIGN KEY (Ride_ID) REFERENCES RIDE(Ride_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT chk_seats_req CHECK (Seats_Requested > 0)
) ENGINE=InnoDB;

-- ============================================================================
-- 5. CHAT TABLE (In-App Messaging between Approved Co-Commuters)
-- ============================================================================
CREATE TABLE CHAT (
    Chat_ID INT AUTO_INCREMENT PRIMARY KEY,
    Request_ID INT NOT NULL,
    Sender_ID INT NOT NULL,
    Receiver_ID INT NOT NULL,
    Message TEXT NOT NULL,
    Sent_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Seen_Status ENUM('Unread', 'Read') NOT NULL DEFAULT 'Unread',
    
    CONSTRAINT fk_chat_request 
        FOREIGN KEY (Request_ID) REFERENCES RIDE_REQUEST(Request_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_chat_sender 
        FOREIGN KEY (Sender_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_chat_receiver 
        FOREIGN KEY (Receiver_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- 6. NOTIFICATION TABLE (System & Activity Alerts)
-- ============================================================================
CREATE TABLE NOTIFICATION (
    Notification_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT NOT NULL,
    Notification_Type ENUM('Ride_Request', 'Request_Accepted', 'Request_Rejected', 'Ride_Cancelled', 'New_Message', 'Friend_Request', 'General') NOT NULL DEFAULT 'General',
    Message VARCHAR(255) NOT NULL,
    Is_Read BOOLEAN NOT NULL DEFAULT FALSE,
    Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_notification_user 
        FOREIGN KEY (User_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- 7. FRIEND TABLE (Social Co-Commuter Connections)
-- ============================================================================
CREATE TABLE FRIEND (
    Friend_ID INT AUTO_INCREMENT PRIMARY KEY,
    Sender_ID INT NOT NULL,
    Receiver_ID INT NOT NULL,
    Friend_Status ENUM('Pending', 'Accepted', 'Blocked') NOT NULL DEFAULT 'Pending',
    Request_Date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_friend_sender 
        FOREIGN KEY (Sender_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_friend_receiver 
        FOREIGN KEY (Receiver_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT uq_friend_pair UNIQUE (Sender_ID, Receiver_ID)
    
) ENGINE=InnoDB;

-- ============================================================================
-- 8. RATING_REVIEW TABLE (5-Star Feedback & Driver/Passenger Rating)
-- ============================================================================
CREATE TABLE RATING_REVIEW (
    Review_ID INT AUTO_INCREMENT PRIMARY KEY,
    Request_ID INT NOT NULL,
    Reviewer_ID INT NOT NULL,
    Reviewee_ID INT NOT NULL,
    Rating INT NOT NULL,
    Comment TEXT NULL,
    Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_review_request 
        FOREIGN KEY (Request_ID) REFERENCES RIDE_REQUEST(Request_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_review_reviewer 
        FOREIGN KEY (Reviewer_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_review_reviewee 
        FOREIGN KEY (Reviewee_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT chk_review_rating CHECK (Rating >= 1 AND Rating <= 5)
) ENGINE=InnoDB;

-- ============================================================================
-- 9. COMMUTE_PASS TABLE (Weekly & Monthly Commute Subscriptions)
-- ============================================================================
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
    
    CONSTRAINT fk_pass_passenger 
        FOREIGN KEY (Passenger_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_pass_host 
        FOREIGN KEY (Host_ID) REFERENCES USER(User_ID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================
CREATE INDEX idx_ride_route ON RIDE(Source, Destination, Date, Ride_Status);
CREATE INDEX idx_ride_driver ON RIDE(Driver_ID);
CREATE INDEX idx_stop_ride ON STOP(Ride_ID, Stop_Order);
CREATE INDEX idx_request_user_ride ON RIDE_REQUEST(User_ID, Ride_ID, Request_Status);
CREATE INDEX idx_chat_request ON CHAT(Request_ID, Sent_Time);
CREATE INDEX idx_notification_user ON NOTIFICATION(User_ID, Is_Read);
CREATE INDEX idx_friend_status ON FRIEND(Sender_ID, Receiver_ID, Friend_Status);
CREATE INDEX idx_review_reviewee ON RATING_REVIEW(Reviewee_ID);
CREATE INDEX idx_pass_host ON COMMUTE_PASS(Host_ID, Pass_Status, Start_Date, End_Date);
