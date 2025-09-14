import os
import json
import re
import webbrowser
from typing import Optional, Dict, List, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Required scopes for full functionality
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

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

def authenticate_google_sheets(force_consent: bool = False, show_progress: bool = True):
    """
    Authenticate and return Google Sheets service object with enhanced UX

    Args:
        force_consent: Force re-authentication even if valid tokens exist
        show_progress: Show progress messages to user
    """
    creds = None

    if not os.path.exists('credentials.json'):
        create_credentials_file()

    # Load existing credentials if available
    if os.path.exists('token.json') and not force_consent:
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if show_progress and creds and creds.valid:
                # Get user info to show connected account
                try:
                    service = build('oauth2', 'v2', credentials=creds)
                    user_info = service.userinfo().get().execute()
                    email = user_info.get('email', 'Unknown')
                    print(f"Google connected as {email}")

                    # Verify scopes
                    if set(SCOPES).issubset(set(creds.scopes or [])):
                        print("All required scopes authorized")
                    else:
                        print("Missing scopes, will re-authenticate...")
                        creds = None
                except:
                    print("Google connected (scope verification skipped)")

        except Exception as e:
            if show_progress:
                print(f"Invalid token file: {e}")
            creds = None

    # Authenticate if no valid credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                if show_progress:
                    print("Refreshing Google authentication...")
                creds.refresh(Request())
                if show_progress:
                    print("Authentication refreshed")
            except Exception as e:
                if show_progress:
                    print(f"Token refresh failed: {e}")
                creds = None

        if not creds:
            if show_progress:
                print("Opening browser for Google sign-in...")
                print("Please authorize access to Google Sheets and Drive")

            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)

                # Use local server for better UX
                creds = flow.run_local_server(
                    port=8080,
                    open_browser=True,
                    success_message='Authorization successful! You can close this tab and return to the application.'
                )

                if show_progress:
                    print("Google authentication successful!")

            except Exception as e:
                if show_progress:
                    print(f"Authentication failed: {e}")
                    print("Troubleshooting:")
                    print("   - Check your credentials.json file")
                    print("   - Ensure OAuth client is configured for 'Desktop application'")
                    print("   - Try running: rm token.json && python google_sheets_auth.py")
                return None

        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build services
    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        return sheets_service, drive_service, creds
    except HttpError as err:
        if show_progress:
            print(f"Failed to build Google services: {err}")
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

def parse_sheet_id_from_url(sheet_input: str) -> Optional[str]:
    """Parse Google Sheet ID from URL or return raw ID"""
    if not sheet_input:
        return None

    # If it's already just an ID (no slashes or dots)
    if '/' not in sheet_input and '.' not in sheet_input and len(sheet_input) > 20:
        return sheet_input.strip()

    # Extract from full URL patterns
    patterns = [
        r'spreadsheets/d/([a-zA-Z0-9-_]+)',  # Standard URL
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',  # Relative URL
        r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)',  # Full domain
    ]

    for pattern in patterns:
        match = re.search(pattern, sheet_input)
        if match:
            return match.group(1)

    return None


def get_sheet_metadata(sheets_service, drive_service, sheet_id: str) -> Optional[Dict]:
    """Get comprehensive sheet metadata including worksheets"""
    try:
        # Get spreadsheet metadata
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=sheet_id,
            includeGridData=False
        ).execute()

        # Get file metadata from Drive for additional info
        try:
            file_info = drive_service.files().get(
                fileId=sheet_id,
                fields="name,owners,createdTime,modifiedTime,webViewLink"
            ).execute()
        except:
            file_info = {}

        # Process worksheets
        sheets = []
        for sheet in spreadsheet.get('sheets', []):
            props = sheet['properties']
            sheets.append({
                'id': props['sheetId'],
                'title': props['title'],
                'index': props['index'],
                'gridProperties': props.get('gridProperties', {}),
                'rowCount': props.get('gridProperties', {}).get('rowCount', 0),
                'columnCount': props.get('gridProperties', {}).get('columnCount', 0)
            })

        return {
            'id': sheet_id,
            'title': spreadsheet.get('properties', {}).get('title', 'Unknown'),
            'locale': spreadsheet.get('properties', {}).get('locale', 'en_US'),
            'sheets': sheets,
            'url': file_info.get('webViewLink', f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit'),
            'owners': file_info.get('owners', []),
            'createdTime': file_info.get('createdTime'),
            'modifiedTime': file_info.get('modifiedTime')
        }

    except HttpError as e:
        if e.resp.status == 403:
            print(f"Access denied to sheet. Please check:")
            print(f"   - Sheet is shared with your Google account")
            print(f"   - You have at least Viewer permissions")
            print(f"   - Sheet ID is correct: {sheet_id}")
        elif e.resp.status == 404:
            print(f"Sheet not found: {sheet_id}")
            print(f"   - Verify the Sheet ID is correct")
            print(f"   - Check that the sheet exists and is not deleted")
        else:
            print(f"Error accessing sheet: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def preview_sheet_data(sheets_service, sheet_id: str, sheet_name: str = None, max_rows: int = 4) -> Optional[Dict]:
    """Get preview of sheet data (headers + first few rows)"""
    try:
        # Build range - if no sheet name provided, use first sheet
        if sheet_name:
            range_name = f"'{sheet_name}'!A1:Z{max_rows}"
        else:
            range_name = f"A1:Z{max_rows}"

        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        # Get total row count for the sheet
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=sheet_id
        ).execute()

        # Find target sheet for row count
        target_sheet = None
        for sheet in spreadsheet.get('sheets', []):
            if not sheet_name or sheet['properties']['title'] == sheet_name:
                target_sheet = sheet['properties']
                break

        total_rows = target_sheet.get('gridProperties', {}).get('rowCount', 0) if target_sheet else len(values)

        return {
            'headers': values[0] if values else [],
            'preview_rows': values[1:] if len(values) > 1 else [],
            'total_rows': max(total_rows - 1, 0),  # Subtract header row
            'sheet_name': sheet_name or 'Sheet1'
        }

    except Exception as e:
        print(f"Error reading sheet preview: {e}")
        return None


def validate_sheet_access(sheets_service, drive_service, sheet_id: str) -> Tuple[bool, Optional[Dict]]:
    """Validate access to sheet and return metadata if successful"""
    try:
        metadata = get_sheet_metadata(sheets_service, drive_service, sheet_id)
        if metadata:
            return True, metadata
        return False, None
    except Exception as e:
        print(f"Sheet validation failed: {e}")
        return False, None


if __name__ == "__main__":
    result = authenticate_google_sheets()

    if result:
        sheets_service, drive_service, creds = result
        print("Successfully authenticated with Google Sheets API!")
        print("\nAvailable functions:")
        print("1. read_sheet(service, spreadsheet_id, range_name)")
        print("2. write_to_sheet(service, spreadsheet_id, range_name, values)")
        print("3. append_to_sheet(service, spreadsheet_id, range_name, values)")
        print("4. create_new_spreadsheet(service, title)")
        print("5. parse_sheet_id_from_url(sheet_input)")
        print("6. get_sheet_metadata(sheets_service, drive_service, sheet_id)")
        print("7. preview_sheet_data(sheets_service, sheet_id, sheet_name)")
    else:
        print("Authentication failed!")