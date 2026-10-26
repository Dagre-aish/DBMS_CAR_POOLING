# 🚗 Carpooling & Ride-Sharing DBMS Project (MySQL)

A complete **Database Management Systems (DBMS)** project developed strictly according to the provided **Entity-Relationship (ER) Diagram** and all **8 Business Rules**.

---

## 📌 Project Architecture

```
DBMS_PROJECT_BY_ANTIGRAVITY/
├── database/
│   ├── 01_schema.sql             # Table DDL, Primary Keys, Foreign Keys, CHECK constraints & Indexes
│   ├── 02_triggers_procedures.sql # Automated Triggers (Rules 7 & 8), Stored Procedures & Views
│   ├── 03_seed_data.sql          # Realistic Mock Data for 10 Users, 8 Rides, Stops, Requests, Chats
│   └── 04_analytical_queries.sql # Advanced SQL Queries (JOINs, Aggregates, Subqueries, Window functions)
├── app/                          # Interactive Full-Stack Web Application (Flask + Tailwind CSS)
│   ├── app.py                    # Flask server & REST API
│   ├── db.py                     # MySQL connection manager with SQLite fallback
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # MySQL configuration template
│   ├── templates/                # Responsive HTML pages
│   └── static/                   # CSS & JS assets
├── docs/
│   ├── DBMS_PROJECT_REPORT.md    # Complete academic project report (ER Mapping, Normalization 1NF-BCNF)
│   └── ER_DIAGRAM_SPECIFICATION.md # ER Model breakdown & cardinality matrix
└── README.md
```

---

## 📋 Entities & Relationships Implemented

| Entity | Primary Key | Foreign Keys & Relationships |
|---|---|---|
| **`USER`** | `User_ID` | Root entity for Drivers and Passengers |
| **`RIDE`** | `Ride_ID` | `Driver_ID` $\to$ `USER(User_ID)` (1:N) |
| **`STOP`** | `Stop_ID` | `Ride_ID` $\to$ `RIDE(Ride_ID)` (1:N) |
| **`RIDE_REQUEST`** | `Request_ID` | `User_ID` $\to$ `USER`, `Ride_ID` $\to$ `RIDE` (1:N) |
| **`CHAT`** | `Chat_ID` | `Request_ID` $\to$ `RIDE_REQUEST`, `Sender_ID` $\to$ `USER`, `Receiver_ID` $\to$ `USER` |
| **`NOTIFICATION`** | `Notification_ID` | `User_ID` $\to$ `USER(User_ID)` (1:N) |
| **`FRIEND`** | `Friend_ID` | `Sender_ID` $\to$ `USER`, `Receiver_ID` $\to$ `USER` (1:N) |

---

## ⚙️ Business Rules Implemented via Database Automation

1. **Rule 1**: A User can create many Rides (`RIDE.Driver_ID -> USER.User_ID`).
2. **Rule 2**: A User can send many Ride Requests (`RIDE_REQUEST.User_ID -> USER.User_ID`).
3. **Rule 3**: A Ride can receive many Ride Requests (`RIDE_REQUEST.Ride_ID -> RIDE.Ride_ID`).
4. **Rule 4**: A User receives many Notifications (`NOTIFICATION.User_ID -> USER.User_ID`).
5. **Rule 5**: A User can send & receive Friend Requests (`FRIEND.Sender_ID` & `FRIEND.Receiver_ID`).
6. **Rule 6**: A Ride can have multiple Stops (`STOP.Ride_ID -> RIDE.Ride_ID` ordered by `Stop_Order`).
7. **Rule 7**: **After a request is accepted, users can chat** (`trg_verify_chat_permission` trigger strictly blocks chats if request is not accepted).
8. **Rule 8**: **Seats are updated based on accepted requests** (`trg_after_ride_request_status_update` trigger automatically decrements `Available_Seats` when accepted, and restores them if cancelled).

---

## 🚀 How to Run the Database in MySQL (Workbench / CLI)

### Method 1: Using MySQL Command Line (CLI)
Open your terminal/command prompt and run the scripts in order:

```bash
# 1. Login to MySQL
mysql -u root -p

# 2. Run Schema Creation
source c:/Users/Aishwarya/Documents/DBMS_PROJECT_BY_ANTIGRAVITY/database/01_schema.sql;

# 3. Compile Triggers, Procedures & Views
source c:/Users/Aishwarya/Documents/DBMS_PROJECT_BY_ANTIGRAVITY/database/02_triggers_procedures.sql;

# 4. Insert Seed Data
source c:/Users/Aishwarya/Documents/DBMS_PROJECT_BY_ANTIGRAVITY/database/03_seed_data.sql;

# 5. Run Analytical Queries & Test Queries
source c:/Users/Aishwarya/Documents/DBMS_PROJECT_BY_ANTIGRAVITY/database/04_analytical_queries.sql;
```

### Method 2: Using MySQL Workbench
1. Open **MySQL Workbench** and connect to your MySQL Server.
2. Go to **File -> Open SQL Script...**
3. Open and execute the files sequentially:
   - `01_schema.sql` (Click the ⚡ **Execute** icon)
   - `02_triggers_procedures.sql` (Click the ⚡ **Execute** icon)
   - `03_seed_data.sql` (Click the ⚡ **Execute** icon)
   - `04_analytical_queries.sql` (Click the ⚡ **Execute** icon)

---

## 💻 How to Run the Interactive Web Application

The project includes an interactive web dashboard where you can post rides, manage bookings, test live seat updates, chat, and run custom queries via an in-browser SQL console.

### 1. Install Dependencies
```bash
cd c:/Users/Aishwarya/Documents/DBMS_PROJECT_BY_ANTIGRAVITY/app
pip install -r requirements.txt
```

### 2. Configure MySQL Connection (Optional)
If running against your local MySQL server, edit/create `.env` in the `app/` folder:
```env
DB_ENGINE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=carpooling_db
```
*(Note: If MySQL server is not running, the application automatically falls back to an embedded SQLite engine with the exact same tables and data so you can test immediately!)*

### 3. Start the Server
```bash
python app.py
```

### 4. Open in Browser
Visit **`http://127.0.0.1:5000`** in any web browser.

---

## 📊 Documentation
- **[Complete DBMS Academic Report](file:///c:/Users/Aishwarya/Documents/DBMS_PROJECT_BY_ANTIGRAVITY/docs/DBMS_PROJECT_REPORT.md)**: Problem formulation, ER-to-Relational mapping rules, and Normalization proofs (1NF $\to$ 2NF $\to$ 3NF / BCNF).
- **[ER Diagram Specification](file:///c:/Users/Aishwarya/Documents/DBMS_PROJECT_BY_ANTIGRAVITY/docs/ER_DIAGRAM_SPECIFICATION.md)**: Detailed ER dictionary, cardinalities, and business rules.
