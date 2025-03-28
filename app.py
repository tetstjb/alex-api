from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

GMAIL_RECOVERY_URL = "https://accounts.google.com/v3/signin/recoveryidentifier?checkConnection=youtube:511&checkedDomains=youtube&ddm=0&dsh=S-418804429:1719166987007523&flowName=WebLiteSignIn&hl=en&pstMsg=1&service=mail"


def check_gmail_availability(email):
    headers = {
        'User-Agent': generate_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    session = requests.Session()
    response = session.get(GMAIL_RECOVERY_URL, headers=headers)
    
    if response.status_code != 200:
        return {"email": email, "status": "Error", "message": "Failed to load Google page"}
    
    if len(email.split("@")[0]) >= 6 and "_" not in email:
        data = {
            'identifier': email
        }
        
        response = session.post(GMAIL_RECOVERY_URL, headers=headers, data=data)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if "Couldn’t find your Google Account" in soup.get_text():
            return {"email": email, "status": "Available"}
        else:
            return {"email": email, "status": "Not Available"}
    else:
        return {"email": email, "status": "Bad format or too short"}


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
