import imaplib
import email
import mysql.connector
import re
import requests
from datetime import datetime
import email.utils
from urllib.parse import urlparse

# Mailbox credentials
MAILBOXES = [
    {"email": "nieuwsbrief@server1.nl", "password": "yourpass", "server": "mail.server1.nl"},
    {"email": "nieuwsbrief@server2.nl", "password": "yourpass", "server": "mail.server2.nl"},
]

# Email subject to filter
SUBJECT_FILTER = "U bent ingeschreven voor de nieuwsbrief"
BODY_PATTERN = re.compile(r"Inschrijving op nieuwsbrief : (\S+)")

# Database setup
DB_CONFIG = {
    "host": "localhost",
    "user": "username",
    "password": "password",
    "database": "databaseName"
}

# Discord Webhook
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOURWEBHOOK"

def init_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            websites TEXT NOT NULL,
            received_at DATETIME NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def send_discord_notification(email, website, received_at):
    message = {
        "embeds": [
            {
                "title": "🎉 New Subscriber!",
                "description": f"**Email:** {email}\n**Source:** {website}\n**Received At:** {received_at}",
                "color": 65280,
            }
        ]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=message)

def extract_domain(email_address):
    return email_address.split('@')[-1]

def save_to_db(email, website, received_at):
    website_domain = extract_domain(website)
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT websites FROM subscribers WHERE email = %s", (email,))
    result = cursor.fetchone()
    
    if result:
        existing_websites = set(result[0].split(", "))
        if website_domain not in existing_websites:
            existing_websites.add(website_domain)
            updated_websites = ", ".join(existing_websites)
            cursor.execute("UPDATE subscribers SET websites = %s, received_at = %s WHERE email = %s", (updated_websites, received_at, email))
            send_discord_notification(email, website_domain, received_at)
    else:
        cursor.execute("INSERT INTO subscribers (email, websites, received_at) VALUES (%s, %s, %s)", (email, website_domain, received_at))
        send_discord_notification(email, website_domain, received_at)
    
    conn.commit()
    cursor.close()
    conn.close()

def parse_email_date(email_date):
    parsed_date = email.utils.parsedate_to_datetime(email_date)
    return parsed_date.strftime('%Y-%m-%d %H:%M:%S')

def check_mailbox(mailbox):
    try:
        mail = imaplib.IMAP4_SSL(mailbox["server"])
        mail.login(mailbox["email"], mailbox["password"])
        mail.select("inbox")
        
        result, data = mail.search(None, '(SUBJECT "' + SUBJECT_FILTER + '")')
        
        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            received_at = parse_email_date(msg["Date"])
            
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        match = BODY_PATTERN.search(body)
                        if match:
                            email_address = match.group(1)
                            save_to_db(email_address, mailbox["email"], received_at)
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                match = BODY_PATTERN.search(body)
                if match:
                    email_address = match.group(1)
                    save_to_db(email_address, mailbox["email"], received_at)
        
        mail.logout()
    except Exception as e:
        print(f"Error processing {mailbox['email']}: {e}")

if __name__ == "__main__":
    init_db()
    for mailbox in MAILBOXES:
        check_mailbox(mailbox)

