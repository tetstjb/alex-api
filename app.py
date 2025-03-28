from flask import Flask, request, jsonify
import mechanize
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

def check_gmail_availability(email):
    gm = mechanize.Browser()
    gm.set_handle_robots(False)
    gm.addheaders = [('User-Agent', generate_user_agent()), ('Accept-Language', 'en-US,en;q=0.9')]
    
    try:
        gm.open("https://accounts.google.com/v3/signin/recoveryidentifier?checkConnection=youtube:511&checkedDomains=youtube&ddm=0&dsh=S-418804429:1719166987007523&flowName=WebLiteSignIn&hl=en&pstMsg=1&service=mail")
        gm.select_form(nr=0)
        
        if len(email.split("@")[0]) >= 6 and "_" not in email:
            gm['identifier'] = email
            response = gm.submit().read()
            soup = BeautifulSoup(response, 'html.parser')
            if "Couldn’t find your Google Account" in soup.get_text():
                return {"email": email, "status": "Available"}
            else:
                return {"email": email, "status": "Not Available"}
        else:
            return {"email": email, "status": "Bad format or too short"}
    except Exception as e:
        return {"email": email, "status": "Error", "message": str(e)}

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
