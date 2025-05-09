from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://mail.google.com/']

flow = InstalledAppFlow.from_client_secrets_file(
    CLIENT_SECRET_FILE, SCOPES)
creds = flow.run_local_server(port=0)

print("\nYour refresh token is:\n")
print(creds.refresh_token)