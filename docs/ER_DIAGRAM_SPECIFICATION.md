# Carpooling & Ride-Sharing System: ER Diagram Specification

This document formally describes the Entity-Relationship (ER) model provided in the architectural design.

---

## 1. Diagram Symbols & Conventions

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Entity      │       │   Relationship  │       │    Attribute    │
│  (Rectangular)  │       │    (Diamond)    │       │     (Oval)      │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

- **Entity Boxes (Green, Blue, Pink, Peach, Yellow, Violet)**: Represent system real-world object categories (`USER`, `RIDE`, `STOP`, `RIDE_REQUEST`, `CHAT`, `NOTIFICATION`, `FRIEND`).
- **Diamond Relations (Beige/Yellow)**: Represent relationships (`Creates`, `Has`, `Sends`, `Receives`, `Generates`).
- **Ovals**: Represent attributes. Underlined attribute names signify **Primary Keys**.
- **Cardinality Markers**: `1` (One) and `M` (Many).

---

## 2. Entity & Attribute Mapping

### 1. `USER` Entity (Green)
- **Primary Key**: `User_ID`
- **Attributes**:
  - `Name` (String)
  - `Email` (Unique String)
  - `Phone_Number` (Unique String)
  - `Password` (Encrypted String)
  - `Gender` (Categorical)
  - `Profile_Picture` (URI/Filename)

### 2. `RIDE` Entity (Blue)
- **Primary Key**: `Ride_ID`
- **Attributes**:
  - `Source` (Starting location)
  - `Destination` (Final drop location)
  - `Date` (Scheduled date of travel)
  - `Time` (Departure time)
  - `Total_Seats` (Total vehicle seating capacity)
  - `Available_Seats` (Remaining vacant seats)
  - `Fare_Per_Seat` (Cost per passenger)
  - `Ride_Status` (`Scheduled`, `Ongoing`, `Completed`, `Cancelled`)

### 3. `STOP` Entity (Pink/Red)
- **Primary Key**: `Stop_ID`
- **Attributes**:
  - `Stop_Name` (Pickup/Drop point name)
  - `Stop_Order` (Sequence number: 1, 2, 3...)
  - `Arrival_Time` (Expected arrival timestamp at stop)

### 4. `RIDE_REQUEST` Entity (Pink)
- **Primary Key**: `Request_ID`
- **Attributes**:
  - `Seats_Requested` (Number of seats needed)
  - `Request_Status` (`Pending`, `Accepted`, `Rejected`, `Cancelled`)
  - `Request_Time` (Submission timestamp)

### 5. `CHAT` Entity (Peach)
- **Primary Key**: `Chat_ID`
- **Attributes**:
  - `Message` (Text content)
  - `Sent_Time` (Dispatch timestamp)
  - `Seen_Status` (`Unread`, `Read`)

### 6. `NOTIFICATION` Entity (Yellow)
- **Primary Key**: `Notification_ID`
- **Attributes**:
  - `Notification_Type` (Alert category)
  - `Message` (Alert description)
  - `Is_Read` (Boolean read status)
  - `Created_At` (Creation timestamp)

### 7. `FRIEND` Entity (Violet)
- **Primary Key**: `Friend_ID`
- **Attributes**:
  - `Friend_Status` (`Pending`, `Accepted`, `Rejected`, `Blocked`)
  - `Request_Date` (Timestamp)

---

## 3. Relationship Cardinality Matrix

| Source Entity | Relationship Name | Target Entity | Source Multiplicity | Target Multiplicity | Semantic Rule |
|---|---|---|---|---|---|
| `USER` | **Creates** | `RIDE` | 1 | M | A user can create many rides. |
| `RIDE` | **Has** | `STOP` | 1 | M | A ride can have multiple intermediate stops. |
| `USER` | **Sends** | `RIDE_REQUEST` | 1 | M | A user can send many ride requests. |
| `RIDE` | **Receives** | `RIDE_REQUEST` | 1 | M | A ride can receive many booking requests. |
| `RIDE_REQUEST` | **Generates** | `CHAT` | 1 | M | An accepted ride request generates chat messages. |
| `USER` | **Sends** | `CHAT` | 1 | M | A user can send multiple chat messages. |
| `USER` | **Receives** | `CHAT` | 1 | M | A user can receive multiple chat messages. |
| `USER` | **Receives** | `NOTIFICATION` | 1 | M | A user receives many notifications. |
| `USER` | **Sends** | `FRIEND` | 1 | M | A user sends friend requests. |
| `USER` | **Receives** | `FRIEND` | 1 | M | A user receives friend requests. |

---

## 4. Business Rules Reference

1. **Rule 1**: A User can create many Rides.
2. **Rule 2**: A User can send many Ride Requests.
3. **Rule 3**: A Ride can receive many Ride Requests.
4. **Rule 4**: A User receives many Notifications.
5. **Rule 5**: A User can send and receive Friend Requests.
6. **Rule 6**: A Ride can have multiple Stops.
7. **Rule 7**: After a request is accepted, users can chat.
8. **Rule 8**: Seats are updated based on accepted requests.
