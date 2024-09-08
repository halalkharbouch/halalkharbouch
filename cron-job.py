import requests
import time

test_email = {'email': 'bilyaminu@gmail.com'}

def ping_frontend():
    try:
        response = requests.get("https://ideas-assess.onrender.com")
        print(f"Frontend status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error pinging frontend: {e}")

def ping_backend():
    try:
        response = requests.post("https://ideasassess.onrender.com/api/auth/check-user-exists/", json=test_email)
        print(f"Backend status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error pinging backend: {e}")

def query_database():
    try:
        response = requests.post("https://ideasassess.onrender.com/api/auth/check-user-exists/", json=test_email)
        print(f"DB query status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error querying database: {e}")

while True:
    ping_frontend()
    ping_backend()
    query_database()
    time.sleep(120)
