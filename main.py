from flask import Flask, request, jsonify
import dns.resolver
import smtplib
import re
import socket
from email.utils import parseaddr

app = Flask(__name__)

# Step 1: Check if email has a valid MX record using a custom DNS resolver
def has_mx_record(email):
    domain = email.split('@')[1]
    try:
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Google's public DNS
        resolver.resolve(domain, 'MX')
        return True
    except:
        return False

# Step 2: Check if email server can accept mail via SMTP
def check_smtp_server(email):
    domain = email.split('@')[1]
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_server = str(mx_records[0].exchange)
        with smtplib.SMTP(mx_server, 25, timeout=10) as server:
            server.helo()
            server.mail('test@example.com')
            code, _ = server.rcpt(email)
            return code == 250
    except:
        return False

# Step 3: Check for role-based emails
def is_role_based_email(email):
    role_based = ['info', 'admin', 'support', 'contact', 'sales', 'help']
    local_part = email.split('@')[0].lower()
    return any(role in local_part for role in role_based)

# Step 4: Basic Email Format Check
def is_valid_format(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(regex, email))

# Step 5: Detect Honeypots
def is_honeypot(email):
    honeypot_patterns = ['test', 'spam', 'catch-all', 'dummy']
    local_part = email.split('@')[0].lower()
    return any(pattern in local_part for pattern in honeypot_patterns)

# Step 6: Main function to validate email
def validate_email(email):
    if not is_valid_format(email):
        return False
    if not has_mx_record(email):
        return False
    if not check_smtp_server(email):
        return False
    if is_role_based_email(email):
        return False
    if is_honeypot(email):
        return False
    return True

@app.route('/validate', methods=['GET'])
def api_validate_email():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'No email provided'}), 400
    result = {
        'email': email,
        'valid_format': is_valid_format(email),
        'has_mx_record': has_mx_record(email),
        'smtp_check': check_smtp_server(email),
        'role_based': is_role_based_email(email),
        'honeypot': is_honeypot(email),
        'valid': validate_email(email)
    }
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
