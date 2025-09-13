# Aethon Data Enricher Setup 🚀

## 🔧 Setup Instructions

### 1. Google Sheets API Configuration

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create/Select Project**: Create a new project or select existing
3. **Enable Google Sheets API**: APIs & Services → Enable APIs → Google Sheets API
4. **Create OAuth Credentials**:
   - Credentials → Create Credentials → OAuth 2.0 Client ID
   - Application type: Desktop application
   - Download the credentials JSON file

5. **Update Authentication**:
   - Replace CLIENT_ID and CLIENT_SECRET in `google_sheets_auth.py`
   - Or place downloaded credentials.json in project directory

### 2. Install Dependencies

```bash
pip install requests beautifulsoup4 google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pandas
```

### 3. Security Configuration

The following files contain sensitive data and are excluded from Git:
- `credentials.json` - Google OAuth credentials
- `token.json` - Authentication tokens
- `enrichment_results_*.json` - Processing results
- `__pycache__/` - Python cache files

### 4. First Run

```bash
# Test authentication
python test_google_sheets.py

# Run demo
python demo_enricher.py

# Analyze your spreadsheet
python test_user_sheet.py
```

## 🚨 Important Notes

- Replace placeholder credentials in `google_sheets_auth.py`
- Never commit actual OAuth credentials to version control
- Respect API rate limits to avoid being blocked
- Test with small datasets before processing large sheets

## ✅ Successfully Tested

This codebase has been successfully tested with:
- Real Google Sheets integration
- 5 rows of professional contact data
- All enrichment features working correctly
- Clean, duplicate-free code structure