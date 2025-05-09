from google_auth_oauthlib.flow import InstalledAppFlow
import os
import json

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://mail.google.com/'
]

def get_refresh_token():
    """Gets a refresh token for Gmail API."""
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json',
        scopes=SCOPES
    )

    # Run the OAuth flow on port 8000
    credentials = flow.run_local_server(
        port=8000,
        access_type='offline',
        prompt='consent'
    )

    # Print the refresh token
    print("\nRefresh Token:", credentials.refresh_token)
    print("\nCopy this refresh token to your .env file")

if __name__ == '__main__':
    get_refresh_token() 