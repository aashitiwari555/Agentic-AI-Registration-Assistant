# 🤖 AI Registration Assistant — Conversational CRUD Chatbot

A conversational AI chatbot that performs full CRUD (Create, Read, Update, Delete) operations on user registration data using an agentic AI workflow, LangChain, Gemini API, and PostgreSQL. The chatbot interacts naturally with users, validates inputs, manages conversation flow intelligently, and securely stores data in a PostgreSQL database.

Built as part of the assignment:
“Conversational Chatbot with Full CRUD Operations Using Agentic AI and PostgreSQL”

---

# 🚀 Features

✅ Conversational registration system  
✅ Full CRUD operations  
✅ AI-powered intent detection  
✅ Multi-turn conversation flow  
✅ PostgreSQL integration  
✅ Validation for email, phone, and DOB  
✅ Error handling and retry flows  
✅ Streamlit chat interface  
✅ Agentic AI workflow using LangChain  
✅ Gemini API integration for natural language understanding  

---

# 🧠 Tech Stack

| Component | Technology |
|---|---|
| Frontend/UI | Streamlit |
| Backend | Python |
| Agentic Framework | LangChain |
| LLM | Gemini API |
| Database | PostgreSQL |
| DB Connector | psycopg2 |
| Environment Config | python-dotenv |
| Validation | regex + datetime |

---

# 📂 Project Structure

```text
chatbot_project/
│
├── app.py
├── agent.py
├── db.py
├── tools.py
├── validators.py
├── prompts.py
├── schema.sql
├── requirements.txt
└── .env
````

---

# 🏗️ System Architecture

```text
User
   ↓
Streamlit UI
   ↓
LangChain Agent
   ↓
Gemini API
   ↓
Intent Detection
   ↓
CRUD Tool Selection
   ↓
Validation Layer
   ↓
PostgreSQL Database
   ↓
Response Returned to User
```

---

# 💬 Supported Operations

## 1️⃣ Create Registration

The chatbot collects:

* Full Name
* Email Address
* Phone Number
* Date of Birth
* Address

Example:

```text
User: I want to register

Bot: Sure! What is your full name?
```

---

## 2️⃣ Read Registration

Users can retrieve their saved registration details using their registered email.

Example:

```text
User: Show my registration details
```

---

## 3️⃣ Update Registration

Users can update fields like:

* Phone Number
* Address

Example:

```text
User: Change my phone number
```

---

## 4️⃣ Delete Registration

Users can permanently remove their registration.

Example:

```text
User: Delete my account
```

---

# 🛡️ Input Validation

The chatbot validates:

| Field        | Validation          |
| ------------ | ------------------- |
| Email        | Proper email format |
| Phone        | 10 digits only      |
| DOB          | YYYY-MM-DD format   |
| Empty Inputs | Prevented           |

Example:

```text
Invalid email format.
Please enter a valid email address.
```

---

# ⚠️ Error Handling

The system handles:

* Invalid inputs
* Duplicate emails
* Missing users
* Database failures
* Empty responses

Example:

```text
⚠ Unable to connect to database.
Please try again later.
```

---

# 🗄️ PostgreSQL Database Schema

Create database:

```sql
CREATE DATABASE registration_chatbot;
```

Create table:

```sql
CREATE TABLE registrations (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    dob DATE NOT NULL,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---



# 🔑 Environment Variables

Create a `.env` file:

```env
DB_NAME=registration_chatbot
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

GOOGLE_API_KEY=your_gemini_api_key
```

---

# ▶️ Running the Application

## Run Streamlit UI

```bash
streamlit run app.py
```

Application opens at:

```text
http://localhost:8501
```

---

# 🧠 Role of LangChain

LangChain acts as the agentic workflow manager.

Responsibilities:

* Managing conversation flow
* Maintaining memory/state
* Routing CRUD operations
* Connecting Gemini with tools
* Handling multi-step conversations

---

# 🤖 Role of Gemini API

Gemini API acts as the language model brain.

Responsibilities:

* Understanding natural language
* Detecting user intent
* Generating conversational responses
* Handling flexible user inputs

---

# 📌 Important Architecture Rule

```text
AI handles conversation
Python handles logic
Database handles storage
```

---

# 🧪 Testing Checklist

## CREATE

* [x] Valid registration
* [x] Invalid email
* [x] Invalid phone
* [x] Duplicate email

---

## READ

* [x] Existing user
* [x] Non-existing user

---

## UPDATE

* [x] Update phone
* [x] Update address

---

## DELETE

* [x] Delete existing user
* [x] Delete non-existing user

---

# 👩‍💻 Author

Aashi Tiwari

```
```
