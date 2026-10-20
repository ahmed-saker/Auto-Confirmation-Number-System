# Auto-Confirmation & Ticketing System 🤖📧

An automated backend system built with **Python** that synchronizes hotel bookings from the **Juniper SOAP API** into an **AWS RDS MySQL database**, continuously monitors for hotel confirmation numbers, and automatically generates and dispatches confirmation emails via **Zoho Desk API** as closed tickets.

---

## 🚀 Key Features

- 🔄 **Automated Data Synchronization** — Fetches new and modified bookings daily from Juniper via SOAP API and securely stores them in a MySQL database.
- 📊 **Database Management** — Uses **MySQL** to track booking statuses, customer details, and confirmation numbers, ensuring no duplicate processing.
- 🔍 **Smart HCN Detection** — Continuously scans the booking remarks for hotel confirmation numbers (HCN) using keyword matching (e.g., "conf", "reference", "confirmed").
- 🎟️ **Auto-Ticketing (Zoho Desk)** — Automatically creates a ticket in Zoho Desk for each newly confirmed booking and sends a highly formatted HTML email to the customer.
- 🧹 **Data Cleansing & Filtering** — Ignores internal/test agencies (e.g., "Global International", "Contracting Test") and handles special edge cases like Key Resorts International (KRI) references.
- ⚡ **Asynchronous API Requests** — Utilizes `asyncio` and `aiohttp` to fetch thousands of booking details from Juniper rapidly.
- 🔁 **Continuous Loop** — Runs seamlessly in a loop, sleeping for 5 minutes between cycles to keep data up-to-date.

---

## 🧰 Tech Stack

| Layer | Tools |
|---|---|
| **Language** | Python 3 |
| **Database** | MySQL (AWS RDS), `pymysql` |
| **Data Manipulation** | `pandas`, `json` |
| **API & Networking** | `requests`, `aiohttp`, `asyncio`, `xmltodict` |
| **APIs Integrated** | Juniper SOAP API (Bookings) · Zoho Desk REST API (Ticketing) |
| **Utilities** | `tqdm`, `retrying`, `datetime` |

---

## ⚙️ System Workflow
┌───────────────────────────────┐
│ 1. Fetch Daily Bookings │
│ (Juniper SOAP API) │
└──────────────┬────────────────┘
▼
┌───────────────────────────────┐
│ 2. Parse & Extract Details │
│ (Async API Calls) │
└──────────────┬────────────────┘
▼
┌───────────────────────────────┐
│ 3. Sync with MySQL Database │
│ (Insert New / Update Old) │
└──────────────┬────────────────┘
▼
┌───────────────────────────────┐
│ 4. Detect Confirmation Numbers│
│ (Keyword Matching) │
└──────────────┬────────────────┘
▼
┌───────────────────────────────┐
│ 5. Create Zoho Desk Tickets │
│ & Send Auto-Emails │
└──────────────┬────────────────┘
▼
┌───────────────────────────────┐
│ 6. Mark as Sent & Sleep 5m │
└───────────────────────────────┘

text

---

## 📂 Project Structure
NewAutoConfirmation.py # Main automation script
mails.xlsx # Excel sheet containing Customer IDs and their corresponding Emails/CCs

text

---

## 🔐 Configuration & Security

Before running the script, **you must replace all sensitive credentials** with your own environment variables or placeholders.

```python
# Juniper Credentials
juniper_user = 'YOUR_JUNIPER_USER'
juniper_pass = 'YOUR_JUNIPER_PASSWORD'

# AWS RDS MySQL Credentials
host = 'YOUR_DB_HOST'
port = 3306
user = 'YOUR_DB_USER'
password = 'YOUR_DB_PASSWORD'
database = 'confirmations'

# Zoho Desk Credentials
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
refresh_token = "YOUR_REFRESH_TOKEN"
org_id = "YOUR_ORG_ID"
⚠️ CRITICAL SECURITY WARNING: The original script contains hardcoded, real-world credentials (Database passwords, OAuth tokens). NEVER commit these to GitHub. Use a .env file and the python-dotenv library to load them securely.

📋 Prerequisites & Requirements
Python 3.8+

Install required packages:

bash
pip install pandas requests aiohttp asyncio xmltodict pymysql retrying tqdm openpyxl
Database Schema: Ensure your MySQL database has a table named bookinglist with the following columns:

Id, Status, BookingCode, BookingDate, LastModifiedDate, AgencyRef, TimeZone, CustomerId, CustomerName, ConfirmationNumber, TravelDate, CustomerEmail, EmailSent.

▶️ How to Run
Ensure mails.xlsx is placed in the correct directory (E:\Users\Administrator\Handover V2\Operations\mails.xlsx).

Run the script:

bash
python NewAutoConfirmation.py
The script will start an infinite loop, checking for new bookings and sending confirmations every 5 minutes.

🛡️ Business Logic & Edge Cases
Ignored Entities: Automatically skips internal accounts like Global International, Contracting Test, and E Commerce.

Key Resorts (KRI) Handling: If the agency reference number matches the confirmation number (which is invalid for KRI), it automatically nullifies the confirmation and avoids sending a false email.

HTML Template: Sends a clean, branded HTML email that includes the Customer Reference, EET Booking Code, and Hotel Confirmation Number.

Ticket Status: The Zoho Desk ticket is created and immediately marked as Closed after the email is sent.

