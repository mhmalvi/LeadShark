import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# OAuth credentials - Replace with your own from Google Cloud Console
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"

def create_credentials_file():
    """Create credentials.json file from CLIENT_ID and CLIENT_SECRET"""
    credentials_dict = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
        }
    }

    with open('credentials.json', 'w') as f:
        json.dump(credentials_dict, f, indent=2)
    print("Created credentials.json file")

def authenticate_google_sheets():
    """Authenticate and return Google Sheets service object"""
    creds = None

    if not os.path.exists('credentials.json'):
        create_credentials_file()

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)
        return service
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None

def read_sheet(service, spreadsheet_id, range_name):
    """Read data from a Google Sheet"""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return []

        return values
    except HttpError as err:
        print(f"An error occurred: {err}")
        return []

def write_to_sheet(service, spreadsheet_id, range_name, values):
    """Write data to a Google Sheet"""
    try:
        body = {
            'values': values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None

def append_to_sheet(service, spreadsheet_id, range_name, values):
    """Append data to a Google Sheet"""
    try:
        body = {
            'values': values
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        print(f"{result.get('updates').get('updatedCells')} cells appended.")
        return result
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None

def create_new_spreadsheet(service, title):
    """Create a new Google Spreadsheet"""
    try:
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        spreadsheet = service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId'
        ).execute()

        print(f"Created spreadsheet with ID: {spreadsheet.get('spreadsheetId')}")
        return spreadsheet.get('spreadsheetId')
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None

if __name__ == "__main__":
    service = authenticate_google_sheets()

    if service:
        print("Successfully authenticated with Google Sheets API!")
        print("\nAvailable functions:")
        print("1. read_sheet(service, spreadsheet_id, range_name)")
        print("2. write_to_sheet(service, spreadsheet_id, range_name, values)")
        print("3. append_to_sheet(service, spreadsheet_id, range_name, values)")
        print("4. create_new_spreadsheet(service, title)")