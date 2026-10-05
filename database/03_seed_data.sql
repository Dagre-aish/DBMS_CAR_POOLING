-- ============================================================================
-- DATABASE MANAGEMENT SYSTEMS PROJECT: COMMUTER CAB-SHARING & CARPOOLING
-- Script 03: Realistic Sample & Seed Dataset (DML)
-- Includes Mumbai & Bengaluru commuter corridors (e.g., Dadar to Ulhasnagar via Thane)
-- ============================================================================

USE carpooling_db;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE CHAT;
TRUNCATE TABLE NOTIFICATION;
TRUNCATE TABLE FRIEND;
TRUNCATE TABLE RIDE_REQUEST;
TRUNCATE TABLE STOP;
TRUNCATE TABLE RIDE;
TRUNCATE TABLE USER;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 1. SEED USERS (Daily Commuters)
-- ============================================================================
INSERT INTO USER (User_ID, Name, Email, Phone_Number, Password, Gender, Profile_Picture, Total_Money_Saved, Created_At) VALUES
(1, 'Aarav Sharma',    'aarav.sharma@example.com',    '+91-9876543210', 'pass123', 'Male',   'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 3450.00, '2026-08-01 09:00:00'),
(2, 'Priya Patel',     'priya.patel@example.com',     '+91-9876543211', 'pass123', 'Female', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150', 4200.00, '2026-08-02 10:15:00'),
(3, 'Rohan Mehta',     'rohan.mehta@example.com',     '+91-9876543212', 'pass123', 'Male',   'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150', 2100.00, '2026-08-03 11:30:00'),
(4, 'Sneha Reddy',     'sneha.reddy@example.com',     '+91-9876543213', 'pass123', 'Female', 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150', 5150.00, '2026-08-04 14:20:00'),
(5, 'Vikram Singh',    'vikram.singh@example.com',    '+91-9876543214', 'pass123', 'Male',   'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150', 1800.00, '2026-08-05 08:45:00'),
(6, 'Ananya Verma',    'ananya.verma@example.com',    '+91-9876543215', 'pass123', 'Female', 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150', 2900.00, '2026-08-06 16:00:00'),
(7, 'Karan Malhotra',  'karan.malhotra@example.com',  '+91-9876543216', 'pass123', 'Male',   'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150', 1250.00, '2026-08-07 12:10:00'),
(8, 'Divya Nair',      'divya.nair@example.com',      '+91-9876543217', 'pass123', 'Female', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150', 3800.00, '2026-08-08 17:35:00'),
(9, 'Amitav Ghosh',    'amitav.ghosh@example.com',    '+91-9876543218', 'pass123', 'Male',   'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150', 4600.00, '2026-08-09 19:00:00'),
(10, 'Ishita Sen',     'ishita.sen@example.com',      '+91-9876543219', 'pass123', 'Female', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150', 2400.00, '2026-08-10 13:25:00');

-- ============================================================================
-- 2. SEED CAB-SHARE & COMMUTE RIDES
-- Includes the flagship Dadar -> Ulhasnagar commute corridor with Thane stop
-- ============================================================================
INSERT INTO RIDE (Ride_ID, Driver_ID, Source, Destination, Date, Time, Total_Seats, Available_Seats, Fare_Per_Seat, Total_Cab_Fare, Ride_Type, Vehicle_Info, Ride_Status, Created_At) VALUES
-- Ride 101: Dadar to Ulhasnagar (Flagship Mumbai Corridor passing Kurla, Mulund, Thane, Kalyan)
(101, 1, 'Dadar, Mumbai',           'Ulhasnagar, Thane District', '2026-08-26', '08:30:00', 4, 2, 220.00, 880.00,  'Cab_Share', 'Uber XL (Ertiga)', 'Scheduled', '2026-08-20 10:00:00'),

-- Ride 102: Bandra West to BKC (Bandra Kurla Complex)
(102, 3, 'Bandra West, Mumbai',     'BKC (Maker Maxity), Mumbai', '2026-08-26', '09:15:00', 3, 2, 90.00,  270.00,  'Auto_Share', 'Shared Auto / Cab', 'Scheduled', '2026-08-21 11:30:00'),

-- Ride 103: Andheri East to Churchgate / Colaba
(103, 5, 'Andheri East, Mumbai',    'Churchgate, South Mumbai',   '2026-08-27', '08:00:00', 4, 3, 250.00, 1000.00, 'Cab_Share', 'Ola Prime Sedan', 'Scheduled', '2026-08-22 09:15:00'),

-- Ride 104: Koramangala to Electronic City (Bengaluru Tech Corridor)
(104, 7, 'Koramangala, Bengaluru',  'Electronic City Phase 1',    '2026-08-26', '08:45:00', 3, 1, 140.00, 420.00,  'Cab_Share', 'Uber Go', 'Scheduled', '2026-08-22 15:40:00'),

-- Ride 105: HSR Layout to Bengaluru Kempegowda Airport
(105, 9, 'HSR Layout, Bengaluru',   'Kempegowda Int. Airport',    '2026-08-27', '14:00:00', 4, 2, 380.00, 1520.00, 'Cab_Share', 'Uber Premier', 'Scheduled', '2026-08-23 18:00:00'),

-- Ride 106: Pune Station to Hinjewadi Phase 1
(106, 1, 'Pune Railway Station',    'Hinjewadi IT Park, Pune',    '2026-08-28', '08:15:00', 3, 3, 180.00, 540.00,  'Cab_Share', 'Ola Sedan', 'Scheduled', '2026-08-24 12:00:00');

-- ============================================================================
-- 3. SEED MULTIPLE WAYPOINTS (STOPS)
-- For Ride 101: Dadar -> Kurla -> Ghatkopar -> Mulund -> Thane -> Dombivli -> Kalyan -> Ulhasnagar
-- ============================================================================
INSERT INTO STOP (Stop_ID, Ride_ID, Stop_Name, Stop_Order, Arrival_Time, Estimated_Sub_Fare, Latitude, Longitude) VALUES
-- Multi-Waypoints for Ride 101 (Dadar -> Ulhasnagar)
(1, 101, 'Kurla Signal (Priyadarshini)', 1, '08:50:00', 60.00,  19.0728, 72.8797),
(2, 101, 'Ghatkopar East (EEH)',         2, '09:05:00', 90.00,  19.0860, 72.9090),
(3, 101, 'Mulund Check Naka',            3, '09:25:00', 130.00, 19.1764, 72.9567),
(4, 101, 'Thane Teen Hath Naka',         4, '09:40:00', 160.00, 19.1872, 72.9692),
(5, 101, 'Dombivli Kalyan Bypass',       5, '10:05:00', 190.00, 19.2183, 73.0867),
(6, 101, 'Kalyan Station Road',          6, '10:20:00', 210.00, 19.2403, 73.1305),

-- Multi-Waypoints for Ride 102 (Bandra to BKC)
(7, 102, 'Kalanagar Junction',           1, '09:22:00', 40.00,  19.0596, 72.8482),
(8, 102, 'BKC ICICI Bank Tower',         2, '09:30:00', 70.00,  19.0662, 72.8660),

-- Multi-Waypoints for Ride 103 (Andheri to Churchgate)
(9,  103, 'Bandra Reclamation Sea Link', 1, '08:25:00', 100.00, 19.0410, 72.8258),
(10, 103, 'Worli Sea Face Point',        2, '08:40:00', 160.00, 19.0176, 72.8150),
(11, 103, 'Haji Ali Circle',             3, '08:55:00', 190.00, 18.9774, 72.8105),

-- Multi-Waypoints for Ride 104 (Koramangala to Electronic City)
(12, 104, 'Silk Board Junction',         1, '09:00:00', 60.00,  12.9176, 77.6238),
(13, 104, 'Bommanahalli Signal',         2, '09:12:00', 90.00,  12.9080, 77.6245),
(14, 104, 'Kudlu Gate',                  3, '09:25:00', 110.00, 12.8887, 77.6443),

-- Multi-Waypoints for Ride 105 (HSR to Kempegowda Airport)
(15, 105, 'Koramangala 80ft Road',       1, '14:20:00', 100.00, 12.9352, 77.6245),
(16, 105, 'Hebbal Flyover',              2, '15:00:00', 250.00, 13.0358, 77.5970),
(17, 105, 'Yelahanka Airforce Base',     3, '15:25:00', 320.00, 13.1007, 77.5963);

-- ============================================================================
-- 4. SEED RIDE_REQUESTS (Booking & Split Requests)
-- ============================================================================
INSERT INTO RIDE_REQUEST (Request_ID, User_ID, Ride_ID, Pickup_Point, Dropoff_Point, Seats_Requested, Agreed_Fare, Request_Status, Request_Time) VALUES
-- En-route booking on Ride 101: Priya travels from Dadar to Thane (Drop-off en route to Ulhasnagar)
(201, 2, 101, 'Dadar, Mumbai', 'Thane Teen Hath Naka', 2, 320.00, 'Accepted', '2026-08-21 14:00:00'),
(202, 4, 101, 'Kurla Signal',  'Ulhasnagar',           1, 200.00, 'Pending',  '2026-08-22 09:30:00'),
(203, 6, 102, 'Bandra West',   'BKC Maker Maxity',     1, 90.00,  'Accepted', '2026-08-23 10:00:00'),
(204, 8, 104, 'Koramangala',   'Silk Board',           1, 60.00,  'Accepted', '2026-08-24 11:30:00'),
(205, 10, 105,'HSR Layout',    'Kempegowda Airport',   2, 760.00, 'Accepted', '2026-08-24 16:00:00');

-- ============================================================================
-- 5. SEED CHAT MESSAGES
-- ============================================================================
INSERT INTO CHAT (Chat_ID, Request_ID, Sender_ID, Receiver_ID, Message, Sent_Time, Seen_Status) VALUES
(301, 201, 2, 1, 'Hi Lavnya! I am sharing your cab till Thane Teen Hath Naka with Shubham. Which pickup spot in Dadar?', '2026-08-21 14:05:00', 'Read'),
(302, 201, 1, 2, 'Hey Priya! I will pick you up outside Dadar TT Circle at 8:30 AM sharp. Uber XL is booked.', '2026-08-21 14:10:00', 'Read'),
(303, 201, 2, 1, 'Great! Saves me ₹300 compared to booking a solo cab. See you tomorrow!', '2026-08-21 14:12:00', 'Read');

-- ============================================================================
-- 6. SEED NOTIFICATIONS
-- ============================================================================
INSERT INTO NOTIFICATION (Notification_ID, User_ID, Notification_Type, Message, Is_Read, Created_At) VALUES
(401, 1, 'Ride_Request', 'Priya Patel requested 2 seat(s) (Dadar to Thane en-route) for your Ulhasnagar cab share.', 1, '2026-08-21 14:00:00'),
(402, 2, 'Request_Accepted', 'Cab Share Confirmed! Aarav accepted your request for Dadar -> Thane. You saved ₹320 on cab fare!', 1, '2026-08-21 14:02:00'),
(403, 4, 'Friend_Accepted', 'Sneha Reddy accepted your friend request.', 1, '2026-08-23 16:30:00');

-- ============================================================================
-- 7. SEED FRIENDS
-- ============================================================================
INSERT INTO FRIEND (Friend_ID, Sender_ID, Receiver_ID, Friend_Status, Request_Date) VALUES
(501, 4, 1, 'Accepted', '2026-08-15 10:00:00'),
(502, 2, 4, 'Accepted', '2026-08-16 11:20:00'),
(503, 1, 3, 'Accepted', '2026-08-18 14:15:00'),
(504, 5, 6, 'Accepted', '2026-08-19 16:40:00'),
(505, 7, 1, 'Pending',  '2026-08-24 09:10:00'),
(506, 8, 2, 'Pending',  '2026-08-24 15:00:00');
