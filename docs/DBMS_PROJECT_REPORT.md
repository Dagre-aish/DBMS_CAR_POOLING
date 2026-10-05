# DATABASE MANAGEMENT SYSTEMS (DBMS) PROJECT REPORT
## Project Title: Ride-Sharing & Carpooling Management System with Social Coordination

---

### Executive Summary
Urban commuting often suffers from severe traffic congestion, high carbon emissions, and escalating fuel costs. This database project designs and implements a centralized, relational **Carpooling & Ride-Sharing Management System** using **MySQL**. The system models the end-to-end workflow of posting rides with intermediate pickup/drop-off stops, managing passenger ride requests with real-time seat tracking, facilitating secure in-app passenger-driver communication, delivering notifications, and managing social friend connections.

---

## 1. Problem Statement & Objectives
- **Centralized Ride Booking**: Allow drivers to publish upcoming itineraries including source, destination, multiple intermediate stops, available seats, and per-seat fare.
- **Seat Availability Tracking**: Ensure that available seats are accurately adjusted in real-time when booking requests are accepted, rejected, or cancelled.
- **Social Coordination & Security**: Enforce privacy and communication rules such that chat is unlocked only after a booking is accepted between the passenger and driver.
- **Auditing & Notifications**: Automatically dispatch system notifications on booking requests, approvals, declines, and friend requests using relational database triggers.

---

## 2. Entity-Relationship (ER) Model Analysis

### 2.1 Entities & Attribute Dictionary

| Entity | Attributes (* = Primary Key) | Description |
|---|---|---|
| **`USER`** | `User_ID`*, `Name`, `Email`, `Phone_Number`, `Password`, `Gender`, `Profile_Picture`, `Created_At` | Represents all system participants (drivers & passengers). |
| **`RIDE`** | `Ride_ID`*, `Driver_ID` (FK), `Source`, `Destination`, `Date`, `Time`, `Total_Seats`, `Available_Seats`, `Fare_Per_Seat`, `Ride_Status`, `Created_At` | Represents vehicle journeys scheduled by a driver. |
| **`STOP`** | `Stop_ID`*, `Ride_ID` (FK), `Stop_Name`, `Stop_Order`, `Arrival_Time` | Ordered intermediate waypoints along a journey route. |
| **`RIDE_REQUEST`** | `Request_ID`*, `User_ID` (FK), `Ride_ID` (FK), `Seats_Requested`, `Request_Status`, `Request_Time` | Booking requests submitted by passengers to drivers. |
| **`CHAT`** | `Chat_ID`*, `Request_ID` (FK), `Sender_ID` (FK), `Receiver_ID` (FK), `Message`, `Sent_Time`, `Seen_Status` | Direct communication thread between matched driver & passenger. |
| **`NOTIFICATION`** | `Notification_ID`*, `User_ID` (FK), `Notification_Type`, `Message`, `Is_Read`, `Created_At` | System alerts for user status updates and requests. |
| **`FRIEND`** | `Friend_ID`*, `Sender_ID` (FK), `Receiver_ID` (FK), `Friend_Status`, `Request_Date` | Peer-to-peer social connections between users. |

---

### 2.2 Cardinality & Structural Constraints
1. **USER — RIDE (1 : N)**: One user (driver) can create zero or many rides; each ride is created by exactly one user.
2. **RIDE — STOP (1 : N)**: One ride can have zero or many intermediate stops; each stop belongs to exactly one ride.
3. **USER — RIDE_REQUEST (1 : N)**: One user (passenger) can send zero or many ride requests; each request originates from one passenger.
4. **RIDE — RIDE_REQUEST (1 : N)**: One ride can receive zero or many ride requests; each request targets one ride.
5. **RIDE_REQUEST — CHAT (1 : N)**: One accepted ride request generates zero or many chat messages; each message belongs to one request.
6. **USER — CHAT (1 : N for Sender, 1 : N for Receiver)**: Users act as senders and receivers of chat messages.
7. **USER — NOTIFICATION (1 : N)**: One user receives zero or many notifications.
8. **USER — FRIEND (1 : N for Sender, 1 : N for Receiver)**: Symmetrical or directed friendship links between distinct user pairs.

---

## 3. ER to Relational Schema Mapping

Applying the standard formal ER-to-Relational mapping rules:
- **Entity Type Mapping**: Each regular entity type maps directly to a relation table with its primary key.
- **1:N Relationship Mapping**: The Primary Key of the "1" side is embedded as a Foreign Key in the "N" side relation.
  - `Driver_ID` in `RIDE` referencing `USER(User_ID)`.
  - `Ride_ID` in `STOP` referencing `RIDE(Ride_ID)`.
  - `User_ID` and `Ride_ID` in `RIDE_REQUEST` referencing `USER(User_ID)` and `RIDE(Ride_ID)`.
  - `User_ID` in `NOTIFICATION` referencing `USER(User_ID)`.
- **Recursive / Dual 1:N Relationships**:
  - `FRIEND` relation includes `Sender_ID` and `Receiver_ID` referencing `USER(User_ID)`.
  - `CHAT` relation includes `Sender_ID` and `Receiver_ID` referencing `USER(User_ID)`.

### Relational Schema (Notation)
- $\text{USER}(\underline{\text{User\_ID}}, \text{Name}, \text{Email}, \text{Phone\_Number}, \text{Password}, \text{Gender}, \text{Profile\_Picture}, \text{Created\_At})$
- $\text{RIDE}(\underline{\text{Ride\_ID}}, \text{Driver\_ID}^{\text{FK}}, \text{Source}, \text{Destination}, \text{Date}, \text{Time}, \text{Total\_Seats}, \text{Available\_Seats}, \text{Fare\_Per\_Seat}, \text{Ride\_Status}, \text{Created\_At})$
- $\text{STOP}(\underline{\text{Stop\_ID}}, \text{Ride\_ID}^{\text{FK}}, \text{Stop\_Name}, \text{Stop\_Order}, \text{Arrival\_Time})$
- $\text{RIDE\_REQUEST}(\underline{\text{Request\_ID}}, \text{User\_ID}^{\text{FK}}, \text{Ride\_ID}^{\text{FK}}, \text{Seats\_Requested}, \text{Request\_Status}, \text{Request\_Time})$
- $\text{CHAT}(\underline{\text{Chat\_ID}}, \text{Request\_ID}^{\text{FK}}, \text{Sender\_ID}^{\text{FK}}, \text{Receiver\_ID}^{\text{FK}}, \text{Message}, \text{Sent\_Time}, \text{Seen\_Status})$
- $\text{NOTIFICATION}(\underline{\text{Notification\_ID}}, \text{User\_ID}^{\text{FK}}, \text{Notification\_Type}, \text{Message}, \text{Is\_Read}, \text{Created\_At})$
- $\text{FRIEND}(\underline{\text{Friend\_ID}}, \text{Sender\_ID}^{\text{FK}}, \text{Receiver\_ID}^{\text{FK}}, \text{Friend\_Status}, \text{Request\_Date})$

---

## 4. Normalization Analysis

### First Normal Form (1NF)
- All attributes contain only atomic values (no repeating groups, multi-valued attributes, or composite records).
- All tables possess designated primary keys.
- *Status: Satisfied.*

### Second Normal Form (2NF)
- The schema is in 1NF.
- Every non-prime attribute is fully functionally dependent on the entire primary key of its relation (no partial functional dependencies).
- *Status: Satisfied.*

### Third Normal Form (3NF) & Boyce-Codd Normal Form (BCNF)
- The schema is in 2NF.
- No transitive functional dependencies exist ($X \to Y$ and $Y \to Z$ where $Z$ is non-prime).
- For every functional dependency $X \to Y$, $X$ is a superkey or candidate key.
- *Status: Satisfied.*

---

## 5. Automated Business Logic: Triggers & Stored Procedures

### 5.1 Business Rule Triggers
1. **Business Rule #8 (Seat Auto-Update)**:
   - Trigger: `trg_after_ride_request_status_update`
   - *Logic*: When `Request_Status` changes to `'Accepted'`, `RIDE.Available_Seats` is decremented by `NEW.Seats_Requested`. If later `'Cancelled'`, seats are incremented back.
2. **Business Rule #7 (Chat Authorization)**:
   - Trigger: `trg_verify_chat_permission`
   - *Logic*: Before inserting a chat message, it queries the referenced `RIDE_REQUEST`. If status is not `'Accepted'`, or if sender/receiver do not match the booking participants, transaction is aborted with SQLSTATE `'45000'`.
3. **Automated Notification Triggers**:
   - `trg_after_ride_request_insert`: Creates notification for driver on incoming booking request.
   - `trg_notify_friend_request`: Creates notification for receiver on new friend request.

### 5.2 Stored Procedures & Transaction Management
- `sp_create_ride`: Handles transactional creation of a ride with seat and fare validation.
- `sp_book_ride`: Atomic check of available capacity, self-booking prevention, and request insertion.
- `sp_respond_ride_request`: Driver verification and state transition handling.
- `sp_search_rides`: Fuzzy multi-criteria search matching route origin, destination, and intermediate stops.

---

## 6. Conclusion
The Carpooling & Ride Sharing database schema strictly models the provided ER diagram while enforcing data integrity through standard normal forms, domain constraints, cascading referential integrity, and automated trigger logic.
