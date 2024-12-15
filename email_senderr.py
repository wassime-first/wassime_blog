import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables from.env file
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
PASSWORD = os.getenv("PASSWORD")
RECEAVER_EMAIL = os.getenv("RECEAVER_EMAIL")


class Email():
    def __init__(self):
        self.smtp_server = 'smtp.gmail.com'  # For Gmail
        self.smtp_port = 587  # TLS port
        self.sender_email = SENDER_EMAIL  # Your email address
        self.password = PASSWORD  # Your email password
        self.receiver_email = RECEAVER_EMAIL  # Recipient's email address

    def message(self, title: str, message: str):

        # Create a multipart email
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg['Subject'] = title

        # Email body
        body = message
        msg.attach(MIMEText(body, 'plain'))

        # Sending the email
        try:
            # Create an SMTP client session object
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Start TLS for security
            server.login(self.sender_email, self.password)  # Log in to your email account
            server.send_message(msg)  # Send the email
            print('Email sent successfully!')
        except Exception as e:
            print(f'Error occurred: {e}')
        finally:
            server.quit()  # Close the connection
