-- ============================================================================
-- DATABASE MANAGEMENT SYSTEMS PROJECT: CARPOOLING & RIDE-SHARING SYSTEM
-- Script 02: Triggers, Stored Procedures, Functions & Views
-- Enforces Business Rules #7, #8, Auto-Notifications, & Business Operations
-- ============================================================================

USE carpooling_db;

DELIMITER //

-- ============================================================================
-- 1. TRIGGERS: AUTOMATED BUSINESS LOGIC
-- ============================================================================

-- ----------------------------------------------------------------------------
-- TRIGGER 1: trg_validate_seats_before_request
-- Rule: Cannot request more seats than currently available in the Ride.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_validate_seats_before_request //
CREATE TRIGGER trg_validate_seats_before_request
BEFORE INSERT ON RIDE_REQUEST
FOR EACH ROW
BEGIN
    DECLARE v_available INT;
    DECLARE v_status VARCHAR(50);
    
    SELECT Available_Seats, Ride_Status 
    INTO v_available, v_status
    FROM RIDE 
    WHERE Ride_ID = NEW.Ride_ID;
    
    IF v_status != 'Scheduled' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Cannot request a ride that is not in Scheduled status.';
    END IF;
    
    IF NEW.Seats_Requested > v_available THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Requested seats exceed available seats for this ride.';
    END IF;
END //

-- ----------------------------------------------------------------------------
-- TRIGGER 2: trg_after_ride_request_insert
-- Action: Automatically create a NOTIFICATION for the Driver when a request arrives.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_after_ride_request_insert //
CREATE TRIGGER trg_after_ride_request_insert
AFTER INSERT ON RIDE_REQUEST
FOR EACH ROW
BEGIN
    DECLARE v_driver_id INT;
    DECLARE v_passenger_name VARCHAR(100);
    DECLARE v_source VARCHAR(150);
    DECLARE v_destination VARCHAR(150);
    
    -- Get Driver & Ride info
    SELECT Driver_ID, Source, Destination 
    INTO v_driver_id, v_source, v_destination
    FROM RIDE 
    WHERE Ride_ID = NEW.Ride_ID;
    
    -- Get Passenger name
    SELECT Name INTO v_passenger_name
    FROM USER 
    WHERE User_ID = NEW.User_ID;
    
    -- Insert notification for driver
    INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read, Created_At)
    VALUES (
        v_driver_id,
        'Ride_Request',
        CONCAT(v_passenger_name, ' requested ', NEW.Seats_Requested, ' seat(s) for your ride from ', v_source, ' to ', v_destination, '.'),
        FALSE,
        NOW()
    );
END //

-- ----------------------------------------------------------------------------
-- TRIGGER 3: trg_after_ride_request_status_update (BUSINESS RULE #8)
-- Rule: "Seats are updated based on accepted requests."
-- When status becomes 'Accepted', deduct available seats.
-- If an accepted request is later 'Cancelled' or 'Rejected', restore seats.
-- Also notifies the passenger about the status change.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_after_ride_request_status_update //
CREATE TRIGGER trg_after_ride_request_status_update
AFTER UPDATE ON RIDE_REQUEST
FOR EACH ROW
BEGIN
    DECLARE v_source VARCHAR(150);
    DECLARE v_destination VARCHAR(150);
    
    SELECT Source, Destination 
    INTO v_source, v_destination
    FROM RIDE 
    WHERE Ride_ID = NEW.Ride_ID;
    
    -- Case A: Request Accepted -> Deduct Available Seats
    IF OLD.Request_Status != 'Accepted' AND NEW.Request_Status = 'Accepted' THEN
        UPDATE RIDE
        SET Available_Seats = Available_Seats - NEW.Seats_Requested
        WHERE Ride_ID = NEW.Ride_ID;
        
        -- Send notification to Passenger
        INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read, Created_At)
        VALUES (
            NEW.User_ID,
            'Request_Accepted',
            CONCAT('Great news! Your request for ', NEW.Seats_Requested, ' seat(s) from ', v_source, ' to ', v_destination, ' was ACCEPTED. You can now chat with your driver.'),
            FALSE,
            NOW()
        );
    END IF;
    
    -- Case B: Request was Accepted but now Cancelled/Rejected -> Restore Available Seats
    IF OLD.Request_Status = 'Accepted' AND (NEW.Request_Status = 'Cancelled' OR NEW.Request_Status = 'Rejected') THEN
        UPDATE RIDE
        SET Available_Seats = Available_Seats + NEW.Seats_Requested
        WHERE Ride_ID = NEW.Ride_ID;
    END IF;
    
    -- Case C: Request Rejected
    IF OLD.Request_Status = 'Pending' AND NEW.Request_Status = 'Rejected' THEN
        INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read, Created_At)
        VALUES (
            NEW.User_ID,
            'Request_Rejected',
            CONCAT('Your ride request for ', v_source, ' to ', v_destination, ' was unfortunately declined by the driver.'),
            FALSE,
            NOW()
        );
    END IF;
END //

-- ----------------------------------------------------------------------------
-- TRIGGER 4: trg_verify_chat_permission (BUSINESS RULE #7)
-- Rule: "After a request is accepted, users can chat."
-- Ensures chat messages can only be sent if the associated Ride_Request is 'Accepted'.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_verify_chat_permission //
CREATE TRIGGER trg_verify_chat_permission
BEFORE INSERT ON CHAT
FOR EACH ROW
BEGIN
    DECLARE v_request_status VARCHAR(50);
    DECLARE v_passenger_id INT;
    DECLARE v_driver_id INT;
    
    -- Get Request status and associated users
    SELECT rr.Request_Status, rr.User_ID, r.Driver_ID
    INTO v_request_status, v_passenger_id, v_driver_id
    FROM RIDE_REQUEST rr
    JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
    WHERE rr.Request_ID = NEW.Request_ID;
    
    -- Check 1: Must be accepted
    IF v_request_status IS NULL OR v_request_status != 'Accepted' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error (Business Rule #7): Chat is only allowed after the ride request has been ACCEPTED.';
    END IF;
    
    -- Check 2: Sender & Receiver must be the Passenger and Driver of this request
    IF NOT (
        (NEW.Sender_ID = v_passenger_id AND NEW.Receiver_ID = v_driver_id) OR
        (NEW.Sender_ID = v_driver_id AND NEW.Receiver_ID = v_passenger_id)
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Chat participants must be the driver and the passenger of the accepted ride request.';
    END IF;
END //

-- ----------------------------------------------------------------------------
-- TRIGGER 5: trg_notify_friend_request
-- Action: Automatically notify receiver when a friend request is sent or accepted.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_notify_friend_request //
CREATE TRIGGER trg_notify_friend_request
AFTER INSERT ON FRIEND
FOR EACH ROW
BEGIN
    DECLARE v_sender_name VARCHAR(100);
    SELECT Name INTO v_sender_name FROM USER WHERE User_ID = NEW.Sender_ID;
    
    INSERT INTO NOTIFICATION (User_ID, Notification_Type, Message, Is_Read, Created_At)
    VALUES (
        NEW.Receiver_ID,
        'Friend_Request',
        CONCAT(v_sender_name, ' sent you a friend request.'),
        FALSE,
        NOW()
    );
END //

-- ============================================================================
-- 2. STORED PROCEDURES: TRANSACTIONAL OPERATIONS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PROCEDURE 1: sp_create_ride
-- Allows a driver to create a new ride with validation.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_create_ride //
CREATE PROCEDURE sp_create_ride(
    IN p_driver_id INT,
    IN p_source VARCHAR(150),
    IN p_destination VARCHAR(150),
    IN p_date DATE,
    IN p_time TIME,
    IN p_total_seats INT,
    IN p_fare DECIMAL(10,2),
    OUT p_ride_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
    
    IF p_total_seats <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Total seats must be greater than 0.';
    END IF;
    
    IF p_fare < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fare cannot be negative.';
    END IF;

    INSERT INTO RIDE (Driver_ID, Source, Destination, Date, Time, Total_Seats, Available_Seats, Fare_Per_Seat, Ride_Status)
    VALUES (p_driver_id, p_source, p_destination, p_date, p_time, p_total_seats, p_total_seats, p_fare, 'Scheduled');
    
    SET p_ride_id = LAST_INSERT_ID();
    
    COMMIT;
END //

-- ----------------------------------------------------------------------------
-- PROCEDURE 2: sp_book_ride
-- Allows a passenger to request seats on a ride.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_book_ride //
CREATE PROCEDURE sp_book_ride(
    IN p_user_id INT,
    IN p_ride_id INT,
    IN p_seats_requested INT,
    OUT p_request_id INT
)
BEGIN
    DECLARE v_driver_id INT;
    DECLARE v_available INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
    
    -- Check if user is trying to book their own ride
    SELECT Driver_ID, Available_Seats INTO v_driver_id, v_available
    FROM RIDE WHERE Ride_ID = p_ride_id;
    
    IF v_driver_id = p_user_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Drivers cannot book requests for their own rides.';
    END IF;
    
    IF p_seats_requested > v_available THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Not enough available seats.';
    END IF;
    
    INSERT INTO RIDE_REQUEST (User_ID, Ride_ID, Seats_Requested, Request_Status, Request_Time)
    VALUES (p_user_id, p_ride_id, p_seats_requested, 'Pending', NOW());
    
    SET p_request_id = LAST_INSERT_ID();
    
    COMMIT;
END //

-- ----------------------------------------------------------------------------
-- PROCEDURE 3: sp_respond_ride_request
-- Allows a driver to Accept or Reject a pending ride request.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_respond_ride_request //
CREATE PROCEDURE sp_respond_ride_request(
    IN p_request_id INT,
    IN p_driver_id INT,
    IN p_decision ENUM('Accepted', 'Rejected')
)
BEGIN
    DECLARE v_actual_driver_id INT;
    DECLARE v_current_status VARCHAR(50);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
    
    SELECT r.Driver_ID, rr.Request_Status
    INTO v_actual_driver_id, v_current_status
    FROM RIDE_REQUEST rr
    JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
    WHERE rr.Request_ID = p_request_id;
    
    IF v_actual_driver_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ride Request not found.';
    END IF;
    
    IF v_actual_driver_id != p_driver_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Unauthorized: Only the driver of this ride can respond.';
    END IF;
    
    IF v_current_status != 'Pending' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This request has already been processed.';
    END IF;
    
    -- Update status (which will trigger trg_after_ride_request_status_update for seat updates)
    UPDATE RIDE_REQUEST
    SET Request_Status = p_decision
    WHERE Request_ID = p_request_id;
    
    COMMIT;
END //

-- ----------------------------------------------------------------------------
-- PROCEDURE 4: sp_search_rides
-- Search rides by source, destination, date, or intermediate stops.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_search_rides //
CREATE PROCEDURE sp_search_rides(
    IN p_source VARCHAR(150),
    IN p_destination VARCHAR(150),
    IN p_date DATE,
    IN p_min_seats INT
)
BEGIN
    SELECT 
        r.Ride_ID,
        r.Source,
        r.Destination,
        r.Date,
        r.Time,
        r.Total_Seats,
        r.Available_Seats,
        r.Fare_Per_Seat,
        r.Ride_Status,
        u.User_ID AS Driver_ID,
        u.Name AS Driver_Name,
        u.Phone_Number AS Driver_Phone,
        u.Profile_Picture AS Driver_Avatar,
        (SELECT COUNT(*) FROM STOP s WHERE s.Ride_ID = r.Ride_ID) AS Total_Stops,
        (SELECT GROUP_CONCAT(s2.Stop_Name ORDER BY s2.Stop_Order ASC SEPARATOR ' ➔ ')
         FROM STOP s2 WHERE s2.Ride_ID = r.Ride_ID) AS Stops_List
    FROM RIDE r
    JOIN USER u ON r.Driver_ID = u.User_ID
    WHERE (p_source IS NULL OR p_source = '' OR r.Source LIKE CONCAT('%', p_source, '%') OR EXISTS (
        SELECT 1 FROM STOP st WHERE st.Ride_ID = r.Ride_ID AND st.Stop_Name LIKE CONCAT('%', p_source, '%')
    ))
    AND (p_destination IS NULL OR p_destination = '' OR r.Destination LIKE CONCAT('%', p_destination, '%') OR EXISTS (
        SELECT 1 FROM STOP st2 WHERE st2.Ride_ID = r.Ride_ID AND st2.Stop_Name LIKE CONCAT('%', p_destination, '%')
    ))
    AND (p_date IS NULL OR r.Date = p_date)
    AND (p_min_seats IS NULL OR r.Available_Seats >= p_min_seats)
    AND r.Ride_Status = 'Scheduled'
    ORDER BY r.Date ASC, r.Time ASC;
END //

DELIMITER ;

-- ============================================================================
-- 3. DATABASE VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- VIEW 1: vw_active_rides_catalog
-- Comprehensive overview of all available rides with Driver & Stops data
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_active_rides_catalog AS
SELECT 
    r.Ride_ID,
    r.Source,
    r.Destination,
    r.Date,
    r.Time,
    r.Total_Seats,
    r.Available_Seats,
    (r.Total_Seats - r.Available_Seats) AS Booked_Seats,
    r.Fare_Per_Seat,
    r.Ride_Status,
    u.User_ID AS Driver_ID,
    u.Name AS Driver_Name,
    u.Email AS Driver_Email,
    u.Phone_Number AS Driver_Phone,
    (SELECT COUNT(*) FROM STOP s WHERE s.Ride_ID = r.Ride_ID) AS Number_Of_Stops,
    (SELECT GROUP_CONCAT(s2.Stop_Name ORDER BY s2.Stop_Order ASC SEPARATOR ' ➔ ') 
     FROM STOP s2 WHERE s2.Ride_ID = r.Ride_ID) AS Route_Itinerary
FROM RIDE r
JOIN USER u ON r.Driver_ID = u.User_ID;

-- ----------------------------------------------------------------------------
-- VIEW 2: vw_ride_requests_detailed
-- Detailed view of requests showing passenger info, driver info, and status
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_ride_requests_detailed AS
SELECT 
    rr.Request_ID,
    rr.Seats_Requested,
    rr.Request_Status,
    rr.Request_Time,
    p.User_ID AS Passenger_ID,
    p.Name AS Passenger_Name,
    p.Email AS Passenger_Email,
    p.Phone_Number AS Passenger_Phone,
    r.Ride_ID,
    r.Source,
    r.Destination,
    r.Date AS Ride_Date,
    r.Time AS Ride_Time,
    r.Fare_Per_Seat,
    (rr.Seats_Requested * r.Fare_Per_Seat) AS Total_Cost,
    d.User_ID AS Driver_ID,
    d.Name AS Driver_Name,
    d.Phone_Number AS Driver_Phone
FROM RIDE_REQUEST rr
JOIN USER p ON rr.User_ID = p.User_ID
JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
JOIN USER d ON r.Driver_ID = d.User_ID;

-- ----------------------------------------------------------------------------
-- VIEW 3: vw_driver_performance_analytics
-- Analytical summary for drivers: Total rides, earnings, occupancy rate
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_driver_performance_analytics AS
SELECT 
    u.User_ID AS Driver_ID,
    u.Name AS Driver_Name,
    u.Email,
    u.Phone_Number,
    COUNT(DISTINCT r.Ride_ID) AS Total_Rides_Offered,
    SUM(CASE WHEN r.Ride_Status = 'Completed' THEN 1 ELSE 0 END) AS Completed_Rides,
    SUM(r.Total_Seats) AS Total_Seat_Capacity,
    SUM(r.Total_Seats - r.Available_Seats) AS Total_Seats_Sold,
    COALESCE(SUM((r.Total_Seats - r.Available_Seats) * r.Fare_Per_Seat), 0.00) AS Estimated_Revenue,
    ROUND(COALESCE((SUM(r.Total_Seats - r.Available_Seats) / NULLIF(SUM(r.Total_Seats), 0)) * 100, 0), 2) AS Occupancy_Rate_Percentage
FROM USER u
LEFT JOIN RIDE r ON u.User_ID = r.Driver_ID
GROUP BY u.User_ID, u.Name, u.Email, u.Phone_Number;

-- ----------------------------------------------------------------------------
-- VIEW 4: vw_user_friends_network
-- Shows accepted friend connections symmetrically
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_user_friends_network AS
SELECT 
    f.Friend_ID,
    f.Sender_ID AS User1_ID,
    u1.Name AS User1_Name,
    f.Receiver_ID AS User2_ID,
    u2.Name AS User2_Name,
    f.Friend_Status,
    f.Request_Date
FROM FRIEND f
JOIN USER u1 ON f.Sender_ID = u1.User_ID
JOIN USER u2 ON f.Receiver_ID = u2.User_ID
WHERE f.Friend_Status = 'Accepted';
