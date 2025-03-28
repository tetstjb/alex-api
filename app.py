from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

GMAIL_RECOVERY_URL = "https://accounts.google.com/_/signup/recovery/identifier"

def check_gmail_availability(email):
    headers = {
        "User-Agent": generate_user_agent(),
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json"
    }
    
    session = requests.Session()
    
    # First request to initialize session
    response = session.get(GMAIL_RECOVERY_URL, headers=headers)
    if response.status_code != 200:
        return {"email": email, "status": "Error", "message": "Failed to load Google page"}
    
    # Check if email format is valid
    if len(email.split("@")[0]) < 6 or "_" in email:
        return {"email": email, "status": "Bad format or too short"}
    
    # Send POST request with the email
    json_data = {"identifier": email}
    response = session.post(GMAIL_RECOVERY_URL, headers=headers, json=json_data)
    
    # Parse response
    soup = BeautifulSoup(response.text, 'html.parser')
    page_text = soup.get_text()

    # Improved response detection
    if "Couldn’t find your Google Account" in page_text or "Find your email" in page_text:
        return {"email": email, "status": "Available"}
    elif "Try another way" in page_text or "Enter the last password you remember" in page_text:
        return {"email": email, "status": "Not Available"}
    else:
        return {"email": email, "status": "Unknown", "message": page_text}


@app.route('/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    if not data or 'emails' not in data:
        return jsonify({"error": "Please provide a list of emails."}), 400
    
    emails = data['emails']
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_gmail_availability, emails))
    
    return jsonify(results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
