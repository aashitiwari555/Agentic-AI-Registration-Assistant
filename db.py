import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def connect_db():
    try:
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return "An account with this email already exists."
    except Exception as e:
        print("Database connection error:", e)

def create_user(full_name, email, phone, dob, address):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = """
        INSERT INTO registrations (full_name, email, phone, dob, address)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (full_name, email, phone, dob, address))
        conn.commit()
        cursor.close()
        conn.close()
        return "User registered successfully"
    except Exception as e:
        return f"Error: {e}"

def get_user(email):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = "SELECT full_name, email, phone, dob, address FROM registrations WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        return f"Error: {e}"

def update_user(email, field, new_value):
    allowed_fields = {"full_name", "email", "phone", "dob", "address"}
    if field not in allowed_fields:
        return "Error: Invalid field modification attempt."
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = f"UPDATE registrations SET {field} = %s WHERE email = %s"
        cursor.execute(query, (new_value, email))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return "No user found with this email."
        conn.commit()
        cursor.close()
        conn.close()
        return "User updated successfully"
    except Exception as e:
        return f"Error: {e}"

def delete_user(email):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = "DELETE FROM registrations WHERE email = %s"
        cursor.execute(query, (email,))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return "No user found with this email."
        conn.commit()
        cursor.close()
        conn.close()
        return "User deleted successfully"
    except Exception as e:
        return f"Error: {e}"