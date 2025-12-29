import requests, os, uuid

ADK_API = os.getenv("ADK_API", "http://localhost:8000")
APP_NAME = os.getenv("ADK_APP_NAME", "my_sample_agent")
USER_ID = os.getenv("ADK_USER_ID", "u_123")

def list_sessions():
    url = f"{ADK_API}/apps/{APP_NAME}/users/{USER_ID}/sessions"
    resp = requests.get(url)
    return resp.json() if resp.status_code == 200 else []

def create_session():
    sid = "s_" + uuid.uuid4().hex[:8]
    url = f"{ADK_API}/apps/{APP_NAME}/users/{USER_ID}/sessions/{sid}"
    requests.post(url, json={})
    return sid

def get_session_events(sid):
    url = f"{ADK_API}/apps/{APP_NAME}/users/{USER_ID}/sessions/{sid}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    return resp.json().get("events", [])

def send_message(sid, message):
    payload = {
        "app_name": APP_NAME,
        "user_id": USER_ID,
        "session_id": sid,
        "new_message": {
            "role": "user",
            "parts": [{"text": message}]
        }
    }
    requests.post(f"{ADK_API}/run", json=payload)

def delete_session(sid):
    url = f"{ADK_API}/apps/{APP_NAME}/users/{USER_ID}/sessions/{sid}"
    requests.delete(url)
