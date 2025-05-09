from django.core.mail.backends.smtp import EmailBackend
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from django.conf import settings
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import os

class GmailOAuth2Backend(EmailBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.credentials = None
        self.refresh_token = settings.GMAIL_OAUTH_REFRESH_TOKEN
        self.client_id = settings.GMAIL_OAUTH_CLIENT_ID
        self.client_secret = settings.GMAIL_OAUTH_CLIENT_SECRET
        self.service = None

    def open(self):
        try:
            self.credentials = Credentials(
                None,  # No access token needed initially
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=['https://www.googleapis.com/auth/gmail.send', 'https://mail.google.com/']
            )

            # Refresh the access token
            if not self.credentials.valid:
                self.credentials.refresh(Request())

            # Create Gmail API service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Error opening connection: {str(e)}")
            return False

    def send_messages(self, email_messages):
        if not self.open():
            return 0

        num_sent = 0
        try:
            for message in email_messages:
                try:
                    # Create message
                    msg = MIMEText(message.body)
                    msg['to'] = ', '.join(message.to)
                    msg['from'] = message.from_email
                    msg['subject'] = message.subject

                    # Encode the message
                    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                    body = {'raw': raw}

                    # Send message
                    self.service.users().messages().send(
                        userId='me',
                        body=body
                    ).execute()

                    num_sent += 1
                except Exception as e:
                    print(f"Error sending message: {str(e)}")
                    if not self.fail_silently:
                        raise
        finally:
            self.close()

        return num_sent

    def close(self):
        if self.service:
            self.service._http.close()