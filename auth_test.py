#!/usr/bin/env python3
"""
LeadShark Authentication Test - Console Flow Only
This script uses console-based OAuth to bypass redirect URI issues
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

def authenticate_console_only():
    """Authenticate using console-only flow"""
    print("=" * 50)
    print("LeadShark - Console Authentication")
    print("=" * 50)
    print()

    creds = None

    # Check for existing valid token
    if os.path.exists('token.json'):
        print("[!] Checking existing token...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if creds and creds.valid:
            print("[OK] Existing token is valid!")
            return test_connection(creds)

        if creds and creds.expired and creds.refresh_token:
            print("[!] Token expired, refreshing...")
            try:
                creds.refresh(Request())
                print("[OK] Token refreshed successfully!")
                save_token(creds)
                return test_connection(creds)
            except Exception as e:
                print(f"[X] Refresh failed: {e}")
                creds = None

    # Need new authentication - console only
    if not creds:
        print("[!] New authentication required")
        print()

        if not os.path.exists('credentials.json'):
            print("[X] credentials.json not found!")
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)

            print("Starting browser authentication...")
            print("This will open your browser automatically.")
            print("If browser doesn't open, copy the URL from the terminal.")
            print()

            # Use local server with available port - should work with current credentials
            creds = flow.run_local_server(
                port=8080,  # Match the port in credentials.json
                open_browser=True,
                success_message='Authentication successful! You can close this tab.'
            )

            if creds:
                save_token(creds)
                print("[OK] Authentication successful!")
                return test_connection(creds)

        except Exception as e:
            print(f"[X] Authentication failed: {e}")
            return False

    return False

def save_token(creds):
    """Save authentication token"""
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("[OK] Token saved")

def test_connection(creds):
    """Test Google Sheets connection"""
    try:
        print("[!] Testing connection...")
        service = build('sheets', 'v4', credentials=creds)

        # Test with configured sheet
        sheet_id = os.getenv('GOOGLE_SHEET_ID', '1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU')

        result = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_title = result.get('properties', {}).get('title', 'Unknown')

        print(f"[OK] Connected to: {sheet_title}")
        print(f"[OK] Sheet ID: {sheet_id}")

        print()
        print("=" * 50)
        print("AUTHENTICATION SUCCESS!")
        print("=" * 50)
        print("Ready to run LeadShark:")
        print("  python simple_compact_test.py")
        print()

        return True

    except Exception as e:
        print(f"[X] Connection failed: {e}")
        return False

if __name__ == "__main__":
    # Set environment
    os.environ['GOOGLE_SHEET_ID'] = '1iop2lVOkA1LsZgrK9tmtCPx_6Mcgr0wkuElWa0wqxeU'

    success = authenticate_console_only()
    if not success:
        print("Authentication failed. Check your credentials.json file.")