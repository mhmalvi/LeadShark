#!/usr/bin/env python3
"""
Manual Google Sheets Authentication for LeadShark
Uses console-based OAuth flow to avoid redirect URI issues
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

def manual_authenticate():
    """Authenticate using console-based flow"""
    print("="*70)
    print("    LeadShark - Manual Authentication")
    print("="*70)
    print()

    creds = None

    # Check for existing token
    if os.path.exists('token.json'):
        print("[!] Existing token found, checking validity...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if creds and creds.valid:
            print("[OK] Existing authentication is still valid!")
            return test_connection(creds)

        if creds and creds.expired and creds.refresh_token:
            print("[!] Token expired, attempting refresh...")
            try:
                creds.refresh(Request())
                print("[OK] Token refreshed successfully!")
                save_token(creds)
                return test_connection(creds)
            except Exception as e:
                print(f"[X] Token refresh failed: {e}")
                creds = None

    # Need new authentication
    if not creds:
        print("[!] New authentication required")
        print()

        if not os.path.exists('credentials.json'):
            print("[X] credentials.json not found!")
            print("    Download from Google Cloud Console")
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)

            print("Choose authentication method:")
            print("1. Browser (may have redirect issues)")
            print("2. Console (copy-paste code)")

            choice = input("Enter choice (1 or 2) [2]: ").strip() or "2"

            if choice == "1":
                print("[!] Opening browser...")
                try:
                    creds = flow.run_local_server(port=0, open_browser=True)
                    print("[OK] Browser authentication successful!")
                except Exception as e:
                    print(f"[X] Browser authentication failed: {e}")
                    print("[!] Falling back to console method...")
                    creds = flow.run_console()
            else:
                print("[!] Using console authentication...")
                print("1. A URL will be displayed")
                print("2. Copy it to your browser")
                print("3. Sign in and authorize")
                print("4. Copy the code back here")
                print()
                creds = flow.run_console()

            if creds:
                save_token(creds)
                print("[OK] Authentication completed!")
                return test_connection(creds)

        except Exception as e:
            print(f"[X] Authentication failed: {e}")
            return False

    return False

def save_token(creds):
    """Save authentication token"""
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("[OK] Token saved for future use")

def test_connection(creds):
    """Test the connection"""
    try:
        print("[!] Testing Google Sheets connection...")
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # Test with configured sheet ID
        sheet_id = os.getenv('GOOGLE_SHEET_ID', '1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU')

        # Get sheet metadata
        result = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_title = result.get('properties', {}).get('title', 'Unknown')

        print(f"[OK] Successfully connected to sheet: {sheet_title}")
        print(f"[OK] Sheet ID: {sheet_id}")

        # Count worksheets
        sheets = result.get('sheets', [])
        print(f"[OK] Found {len(sheets)} worksheets")

        for sheet in sheets:
            props = sheet['properties']
            print(f"     - {props['title']}: {props.get('gridProperties', {}).get('rowCount', 0)} rows")

        print()
        print("="*70)
        print("AUTHENTICATION SUCCESSFUL!")
        print("="*70)
        print("You can now run LeadShark:")
        print("  python simple_compact_test.py")
        print("  python run_pipeline.py")
        print()

        return True

    except Exception as e:
        print(f"[X] Connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Set environment variable
    os.environ['GOOGLE_SHEET_ID'] = '1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU'

    success = manual_authenticate()

    if success:
        print("Ready to run LeadShark!")
    else:
        print("Authentication failed. Please check your setup.")