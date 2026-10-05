-- ============================================================================
-- DATABASE MANAGEMENT SYSTEMS PROJECT: CARPOOLING & RIDE-SHARING SYSTEM
-- Script 04: Advanced Analytical SQL Queries, Reports & Trigger Verifications
-- Demonstrates complex joins, aggregations, subqueries, and window functions
-- ============================================================================

USE carpooling_db;

-- ============================================================================
-- QUERY 1: Multi-Table JOIN (Rides with Driver details and Itinerary Stops)
-- Description: Retrieves full details of upcoming scheduled rides, combining
--              Driver profile info and intermediate stops formatted in route order.
-- ============================================================================
SELECT 
    r.Ride_ID,
    r.Source AS Origin,
    r.Destination,
    r.Date AS Travel_Date,
    r.Time AS Departure_Time,
    r.Available_Seats,
    r.Total_Seats,
    CONCAT('₹', r.Fare_Per_Seat) AS Fare,
    u.Name AS Driver_Name,
    u.Phone_Number AS Driver_Contact,
    COALESCE(GROUP_CONCAT(CONCAT(s.Stop_Order, '. ', s.Stop_Name, ' (', TIME_FORMAT(s.Arrival_Time, '%H:%i'), ')') ORDER BY s.Stop_Order SEPARATOR '  ➔  '), 'Direct Route (No intermediate stops)') AS Route_Stops
FROM RIDE r
JOIN USER u ON r.Driver_ID = u.User_ID
LEFT JOIN STOP s ON r.Ride_ID = s.Ride_ID
WHERE r.Ride_Status = 'Scheduled'
GROUP BY r.Ride_ID, r.Source, r.Destination, r.Date, r.Time, r.Available_Seats, r.Total_Seats, r.Fare_Per_Seat, u.Name, u.Phone_Number
ORDER BY r.Date ASC, r.Time ASC;

-- ============================================================================
-- QUERY 2: Driver Earnings & Performance Analysis (Aggregation with GROUP BY & HAVING)
-- Description: Calculates total rides, seats occupied, total revenue earned,
--              and average fare per seat for each active driver.
-- ============================================================================
SELECT 
    u.User_ID AS Driver_ID,
    u.Name AS Driver_Name,
    COUNT(r.Ride_ID) AS Total_Rides_Hosted,
    SUM(r.Total_Seats - r.Available_Seats) AS Total_Passengers_Booked,
    SUM((r.Total_Seats - r.Available_Seats) * r.Fare_Per_Seat) AS Total_Revenue_Earned,
    ROUND(AVG(r.Fare_Per_Seat), 2) AS Average_Fare_Rate,
    ROUND(SUM(r.Total_Seats - r.Available_Seats) / SUM(r.Total_Seats) * 100, 1) AS Seat_Occupancy_Rate_Pct
FROM USER u
JOIN RIDE r ON u.User_ID = r.Driver_ID
GROUP BY u.User_ID, u.Name
HAVING Total_Rides_Hosted >= 1
ORDER BY Total_Revenue_Earned DESC;

-- ============================================================================
-- QUERY 3: Passenger Booking Summary with Total Cost & Driver Contact
-- Description: Retrieves detailed list of bookings made by passengers,
--              including computed total trip fare and current request status.
-- ============================================================================
SELECT 
    rr.Request_ID,
    p.Name AS Passenger_Name,
    p.Email AS Passenger_Email,
    p.Phone_Number AS Passenger_Phone,
    d.Name AS Driver_Name,
    r.Source AS Pickup_Location,
    r.Destination AS Drop_Location,
    r.Date AS Travel_Date,
    rr.Seats_Requested,
    r.Fare_Per_Seat,
    (rr.Seats_Requested * r.Fare_Per_Seat) AS Total_Trip_Cost,
    rr.Request_Status,
    rr.Request_Time
FROM RIDE_REQUEST rr
JOIN USER p ON rr.User_ID = p.User_ID
JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
JOIN USER d ON r.Driver_ID = d.User_ID
ORDER BY rr.Request_Time DESC;

-- ============================================================================
-- QUERY 4: Correlated Subquery - Find Users with Highest Accepted Bookings
-- Description: Identifies frequent travelers who have at least 2 accepted rides.
-- ============================================================================
SELECT 
    u.User_ID,
    u.Name,
    u.Email,
    u.Phone_Number,
    (SELECT COUNT(*) 
     FROM RIDE_REQUEST rr 
     WHERE rr.User_ID = u.User_ID AND rr.Request_Status = 'Accepted') AS Total_Accepted_Rides,
    (SELECT COALESCE(SUM(rr.Seats_Requested * r.Fare_Per_Seat), 0)
     FROM RIDE_REQUEST rr 
     JOIN RIDE r ON rr.Ride_ID = r.Ride_ID
     WHERE rr.User_ID = u.User_ID AND rr.Request_Status = 'Accepted') AS Total_Spent_On_Rides
FROM USER u
WHERE (SELECT COUNT(*) FROM RIDE_REQUEST rr WHERE rr.User_ID = u.User_ID AND rr.Request_Status = 'Accepted') >= 1
ORDER BY Total_Accepted_Rides DESC, Total_Spent_On_Rides DESC;

-- ============================================================================
-- QUERY 5: Window Functions - Ranking Drivers by Total Revenue
-- Description: Uses DENSE_RANK() to assign rank to drivers based on gross earnings.
-- ============================================================================
SELECT 
    u.User_ID,
    u.Name AS Driver_Name,
    COUNT(r.Ride_ID) AS Total_Rides,
    COALESCE(SUM((r.Total_Seats - r.Available_Seats) * r.Fare_Per_Seat), 0) AS Gross_Earnings,
    DENSE_RANK() OVER (ORDER BY COALESCE(SUM((r.Total_Seats - r.Available_Seats) * r.Fare_Per_Seat), 0) DESC) AS Revenue_Rank
FROM USER u
JOIN RIDE r ON u.User_ID = r.Driver_ID
GROUP BY u.User_ID, u.Name;

-- ============================================================================
-- QUERY 6: Social Connections - Mutual & Accepted Friends List
-- Description: Queries symmetric friendship network for a specific user (User_ID = 1).
-- ============================================================================
SELECT 
    f.Friend_ID,
    CASE 
        WHEN f.Sender_ID = 1 THEN u2.Name 
        ELSE u1.Name 
    END AS Friend_Name,
    CASE 
        WHEN f.Sender_ID = 1 THEN u2.Email 
        ELSE u1.Email 
    END AS Friend_Email,
    CASE 
        WHEN f.Sender_ID = 1 THEN u2.Phone_Number 
        ELSE u1.Phone_Number 
    END AS Friend_Phone,
    f.Friend_Status,
    f.Request_Date
FROM FRIEND f
JOIN USER u1 ON f.Sender_ID = u1.User_ID
JOIN USER u2 ON f.Receiver_ID = u2.User_ID
WHERE (f.Sender_ID = 1 OR f.Receiver_ID = 1) 
  AND f.Friend_Status = 'Accepted';

-- ============================================================================
-- QUERY 7: Unread Notifications Count Per User
-- Description: Summarizes unread alerts for dashboard notification badges.
-- ============================================================================
SELECT 
    u.User_ID,
    u.Name,
    u.Email,
    COUNT(n.Notification_ID) AS Total_Notifications,
    SUM(CASE WHEN n.Is_Read = FALSE THEN 1 ELSE 0 END) AS Unread_Count
FROM USER u
LEFT JOIN NOTIFICATION n ON u.User_ID = n.User_ID
GROUP BY u.User_ID, u.Name, u.Email
ORDER BY Unread_Count DESC;

-- ============================================================================
-- QUERY 8: Chat Log Between Passenger and Driver for an Accepted Ride Request
-- Description: Retrieves conversation transcript in chronological order for Request_ID = 201.
-- ============================================================================
SELECT 
    c.Chat_ID,
    c.Request_ID,
    s.Name AS Sender,
    r.Name AS Receiver,
    c.Message,
    DATE_FORMAT(c.Sent_Time, '%d %b %Y, %h:%i %p') AS Formatted_Time,
    c.Seen_Status
FROM CHAT c
JOIN USER s ON c.Sender_ID = s.User_ID
JOIN USER r ON c.Receiver_ID = r.User_ID
WHERE c.Request_ID = 201
ORDER BY c.Sent_Time ASC;
