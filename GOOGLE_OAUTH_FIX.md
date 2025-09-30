# Google OAuth Redirect URI Fix

## The Problem
You're getting "Error 400: redirect_uri_mismatch" because your Google Cloud Console OAuth client doesn't have the correct redirect URIs configured.

## The Solution

### Step 1: Update Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" → "Credentials"
3. Find your OAuth 2.0 Client ID (the one matching your client_id: `430174413608-l9nvo8lhe5tp90vfu2brth3hs7t5bl69.apps.googleusercontent.com`)
4. Click on it to edit
5. Under "Authorized redirect URIs", add these URIs:
   ```
   http://localhost:8080/
   http://localhost:8000/
   http://localhost/
   ```
6. Click "Save"

### Step 2: Test Authentication
After updating the redirect URIs, run:
```bash
python auth_test.py
```

### Step 3: Run LeadShark
Once authenticated, run:
```bash
python simple_compact_test.py
```

## Alternative: Manual Authentication
If you still have issues, use the manual authentication script:
```bash
python manual_auth.py
```
This uses a console-based flow that doesn't require redirect URIs.

## Files Updated
- ✅ `credentials.json` - Already has correct redirect URIs
- ✅ `google_sheets_auth.py` - Updated authentication flow
- ✅ `auth_test.py` - Created simple auth test
- ✅ `manual_auth.py` - Console-based authentication backup

## Ready to Run
All code changes are complete. You just need to update the Google Cloud Console redirect URIs and you'll be ready to run LeadShark!