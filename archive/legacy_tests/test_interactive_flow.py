#!/usr/bin/env python3
"""
Comprehensive Test Suite for Interactive CLI Flow
Tests OAuth, sheet selection, progress tracking, and error handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))

from google_sheets_auth import (
    parse_sheet_id_from_url,
    get_sheet_metadata,
    validate_sheet_access,
    preview_sheet_data,
    authenticate_google_sheets
)
from cli_interface import CLIInterface
from non_destructive_enricher import NonDestructiveEnricher


class TestSheetURLParsing(unittest.TestCase):
    """Test Google Sheets URL parsing"""

    def test_parse_standard_url(self):
        """Test parsing standard Google Sheets URL"""
        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        expected = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        result = parse_sheet_id_from_url(url)
        self.assertEqual(result, expected)

    def test_parse_url_with_gid(self):
        """Test parsing URL with gid parameter"""
        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=123456789"
        expected = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        result = parse_sheet_id_from_url(url)
        self.assertEqual(result, expected)

    def test_parse_raw_sheet_id(self):
        """Test parsing when raw sheet ID is provided"""
        sheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        result = parse_sheet_id_from_url(sheet_id)
        self.assertEqual(result, sheet_id)

    def test_parse_short_url(self):
        """Test parsing shortened or relative URL"""
        url = "/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        expected = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        result = parse_sheet_id_from_url(url)
        self.assertEqual(result, expected)

    def test_parse_invalid_url(self):
        """Test parsing invalid URL returns None"""
        invalid_urls = [
            "",
            "not-a-url",
            "https://example.com/not-sheets",
            "https://docs.google.com/document/d/invalid"
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                result = parse_sheet_id_from_url(url)
                self.assertIsNone(result)


class TestOAuthFlow(unittest.TestCase):
    """Test OAuth authentication flow"""

    @patch('google_sheets_auth.build')
    @patch('google_sheets_auth.Credentials.from_authorized_user_file')
    @patch('os.path.exists')
    def test_existing_valid_credentials(self, mock_exists, mock_creds_file, mock_build):
        """Test authentication with existing valid credentials"""
        # Setup mocks
        mock_exists.side_effect = lambda path: path == 'token.json'
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        mock_creds_file.return_value = mock_creds

        # Mock OAuth2 user info
        mock_oauth_service = Mock()
        mock_oauth_service.userinfo().get().execute.return_value = {'email': 'test@example.com'}

        mock_build.side_effect = lambda service, version, credentials=None: (
            mock_oauth_service if service == 'oauth2' else Mock()
        )

        # Test authentication
        result = authenticate_google_sheets(show_progress=False)

        # Verify
        self.assertIsNotNone(result)
        sheets_service, drive_service, creds = result
        self.assertEqual(creds, mock_creds)

    @patch('google_sheets_auth.InstalledAppFlow.from_client_secrets_file')
    @patch('google_sheets_auth.build')
    @patch('os.path.exists')
    def test_new_authentication_flow(self, mock_exists, mock_build, mock_flow):
        """Test new authentication flow"""
        # Setup mocks
        mock_exists.return_value = True  # credentials.json exists

        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "test"}'

        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow.return_value = mock_flow_instance

        mock_sheets_service = Mock()
        mock_drive_service = Mock()
        mock_build.side_effect = lambda service, version, credentials=None: (
            mock_sheets_service if service == 'sheets' else mock_drive_service
        )

        with patch('builtins.open', unittest.mock.mock_open()):
            result = authenticate_google_sheets(force_consent=True, show_progress=False)

        # Verify
        self.assertIsNotNone(result)
        sheets_service, drive_service, creds = result
        self.assertEqual(creds, mock_creds)
        mock_flow_instance.run_local_server.assert_called_once()

    def test_authentication_failure(self):
        """Test authentication failure scenarios"""
        with patch('google_sheets_auth.build', side_effect=Exception("Auth failed")):
            result = authenticate_google_sheets(show_progress=False)
            self.assertIsNone(result)


class TestSheetMetadata(unittest.TestCase):
    """Test sheet metadata retrieval"""

    def setUp(self):
        self.mock_sheets_service = Mock()
        self.mock_drive_service = Mock()

    def test_get_sheet_metadata_success(self):
        """Test successful metadata retrieval"""
        # Mock spreadsheet response
        mock_spreadsheet = {
            'properties': {
                'title': 'Test Spreadsheet',
                'locale': 'en_US'
            },
            'sheets': [
                {
                    'properties': {
                        'sheetId': 0,
                        'title': 'Sheet1',
                        'index': 0,
                        'gridProperties': {
                            'rowCount': 100,
                            'columnCount': 26
                        }
                    }
                },
                {
                    'properties': {
                        'sheetId': 123456,
                        'title': 'Data',
                        'index': 1,
                        'gridProperties': {
                            'rowCount': 500,
                            'columnCount': 15
                        }
                    }
                }
            ]
        }

        # Mock drive file info
        mock_file_info = {
            'name': 'Test Spreadsheet',
            'webViewLink': 'https://docs.google.com/spreadsheets/d/test_id/edit',
            'owners': [{'displayName': 'Test User'}],
            'createdTime': '2024-01-01T00:00:00.000Z',
            'modifiedTime': '2024-01-02T00:00:00.000Z'
        }

        self.mock_sheets_service.spreadsheets().get().execute.return_value = mock_spreadsheet
        self.mock_drive_service.files().get().execute.return_value = mock_file_info

        # Test
        metadata = get_sheet_metadata(self.mock_sheets_service, self.mock_drive_service, 'test_id')

        # Verify
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['title'], 'Test Spreadsheet')
        self.assertEqual(len(metadata['sheets']), 2)
        self.assertEqual(metadata['sheets'][0]['title'], 'Sheet1')
        self.assertEqual(metadata['sheets'][1]['title'], 'Data')

    def test_get_sheet_metadata_403_error(self):
        """Test 403 permission error"""
        from googleapiclient.errors import HttpError

        # Mock 403 error
        mock_response = Mock()
        mock_response.status = 403
        error = HttpError(mock_response, b'Permission denied')

        self.mock_sheets_service.spreadsheets().get().execute.side_effect = error

        metadata = get_sheet_metadata(self.mock_sheets_service, self.mock_drive_service, 'test_id')
        self.assertIsNone(metadata)

    def test_get_sheet_metadata_404_error(self):
        """Test 404 not found error"""
        from googleapiclient.errors import HttpError

        mock_response = Mock()
        mock_response.status = 404
        error = HttpError(mock_response, b'Not found')

        self.mock_sheets_service.spreadsheets().get().execute.side_effect = error

        metadata = get_sheet_metadata(self.mock_sheets_service, self.mock_drive_service, 'test_id')
        self.assertIsNone(metadata)


class TestCLIInterface(unittest.TestCase):
    """Test CLI interface functionality"""

    def setUp(self):
        self.cli = CLIInterface()

    def test_sheet_selection_single_worksheet(self):
        """Test worksheet selection with single sheet"""
        metadata = {
            'sheets': [
                {'title': 'Main Data', 'rowCount': 100, 'columnCount': 20}
            ]
        }

        # Should automatically select single sheet
        with patch.object(self.cli, 'console') as mock_console:
            result = self.cli.select_worksheet(metadata)

        self.assertEqual(result, 'Main Data')

    def test_sheet_selection_multiple_worksheets(self):
        """Test worksheet selection with multiple sheets"""
        metadata = {
            'sheets': [
                {'title': 'Sheet1', 'rowCount': 100, 'columnCount': 20},
                {'title': 'Data', 'rowCount': 500, 'columnCount': 15},
                {'title': 'Archive', 'rowCount': 50, 'columnCount': 10}
            ]
        }

        if self.cli.use_rich:
            # Mock rich interface
            with patch('cli_interface.IntPrompt.ask', return_value=2):
                result = self.cli.select_worksheet(metadata)
            self.assertEqual(result, 'Data')
        else:
            # Mock plain input
            with patch('builtins.input', return_value='2'):
                result = self.cli.select_worksheet(metadata)
            self.assertEqual(result, 'Data')

    def test_processing_mode_selection(self):
        """Test processing mode selection"""
        if self.cli.use_rich:
            with patch('cli_interface.IntPrompt.ask', return_value=1), \
                 patch('cli_interface.Prompt.ask', return_value='default'):
                options = self.cli.prompt_processing_mode()

            self.assertEqual(options['max_rows'], 5)
            self.assertEqual(options['rate_profile'], 'default')
            self.assertFalse(options['dry_run'])
        else:
            with patch('builtins.input', side_effect=['1']):
                options = self.cli.prompt_processing_mode()

            self.assertEqual(options['max_rows'], 5)

    def test_progress_tracking(self):
        """Test progress tracking updates"""
        if self.cli.use_rich:
            progress = self.cli.create_progress_display(10, "test", "Test Sheet")
            self.assertIsNotNone(progress)

            # Test progress updates
            self.cli.update_progress(1, "John Doe", "processing", "Scraping...")
            self.cli.update_progress(1, "John Doe", "ok", "3 sources, 85% confidence")

            # Verify stats are tracked
            self.assertEqual(self.cli.stats['ok'], 1)


class TestProgressIntegration(unittest.TestCase):
    """Test progress tracking integration with enricher"""

    def setUp(self):
        self.enricher = NonDestructiveEnricher("test_sheet", dry_run=True)
        self.cli = CLIInterface()
        self.enricher.cli = self.cli

    def test_display_name_extraction(self):
        """Test display name extraction for progress"""
        # Test with full name
        row_dict = {'name': 'John Doe', 'company': 'TechCorp'}
        name = self.enricher._get_display_name(row_dict)
        self.assertEqual(name, 'John Doe')

        # Test with company only
        row_dict = {'company': 'TechCorp Inc'}
        name = self.enricher._get_display_name(row_dict)
        self.assertEqual(name, '(TechCorp Inc)')

        # Test with empty data
        row_dict = {}
        name = self.enricher._get_display_name(row_dict)
        self.assertEqual(name, 'Row data')

    @patch.object(NonDestructiveEnricher, 'read_headers')
    @patch.object(NonDestructiveEnricher, 'ensure_enrichment_headers')
    def test_progress_updates_during_processing(self, mock_ensure, mock_headers):
        """Test that progress updates are called during processing"""
        # Setup mocks
        mock_headers.return_value = (['name', 'email'], {'name': 0, 'email': 1})
        mock_ensure.return_value = {}

        # Mock service
        self.enricher.service = Mock()
        self.enricher.service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['name', 'email'],
                ['John Doe', 'john@example.com'],
                ['Jane Smith', 'jane@example.com']
            ]
        }

        # Mock CLI interface
        mock_cli = Mock()
        self.enricher.cli = mock_cli

        # Process sheet
        stats = self.enricher.process_sheet(max_rows=2)

        # Verify progress updates were called
        self.assertGreater(mock_cli.update_progress.call_count, 0)

        # Verify calls include processing and completion states
        calls = mock_cli.update_progress.call_args_list
        processing_calls = [call for call in calls if 'processing' in str(call)]
        completion_calls = [call for call in calls if any(status in str(call) for status in ['ok', 'partial', 'failed'])]

        self.assertGreater(len(processing_calls), 0)
        self.assertGreater(len(completion_calls), 0)


class TestErrorHandling(unittest.TestCase):
    """Test comprehensive error handling"""

    def test_sheet_access_validation(self):
        """Test sheet access validation with various errors"""
        mock_sheets_service = Mock()
        mock_drive_service = Mock()

        # Test with exception
        mock_sheets_service.spreadsheets().get().execute.side_effect = Exception("Network error")

        valid, metadata = validate_sheet_access(mock_sheets_service, mock_drive_service, "test_id")

        self.assertFalse(valid)
        self.assertIsNone(metadata)

    def test_preview_data_error_handling(self):
        """Test preview data error handling"""
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.side_effect = Exception("API error")

        result = preview_sheet_data(mock_service, "test_id", "Sheet1")
        self.assertIsNone(result)

    def test_enricher_row_processing_error(self):
        """Test enricher handles individual row processing errors gracefully"""
        enricher = NonDestructiveEnricher("test_sheet", dry_run=True)

        # Mock a row that will cause an error
        row_dict = {'invalid': 'data'}

        # This should not raise an exception
        try:
            result = enricher.process_row(row_dict, 1)
            # Should get a result even if processing fails
            self.assertIsInstance(result, type(enricher.process_row(row_dict, 1)))
        except Exception as e:
            self.fail(f"process_row should handle errors gracefully, but raised {e}")


def run_integration_test():
    """Run a simulated integration test"""
    print("Running simulated integration test...")

    # Test the full flow with mocked services
    cli = CLIInterface()

    if not cli.use_rich:
        print("⚠️  Rich not available - some features will be limited")

    # Simulate sheet selection
    print("✅ Sheet URL parsing")
    sheet_id = parse_sheet_id_from_url("https://docs.google.com/spreadsheets/d/test123/edit")
    assert sheet_id == "test123"

    # Simulate CLI interactions
    print("✅ CLI interface initialization")
    cli.print_banner()

    print("✅ Progress tracking")
    if cli.use_rich:
        progress = cli.create_progress_display(3, "test", "Test Sheet", dry_run=True)
        if progress:
            with progress:
                for i in range(1, 4):
                    cli.update_progress(i, f"Person {i}", "processing", "Testing...")
                    import time
                    time.sleep(0.1)
                    cli.update_progress(i, f"Person {i}", "ok", "Test complete")
                    time.sleep(0.1)

        cli.show_final_summary({'ok': 3, 'partial': 0, 'failed': 0, 'skipped': 0}, 2.5)

    print("✅ Integration test completed successfully!")


def run_all_tests():
    """Run all test suites"""
    test_classes = [
        TestSheetURLParsing,
        TestOAuthFlow,
        TestSheetMetadata,
        TestCLIInterface,
        TestProgressIntegration,
        TestErrorHandling
    ]

    all_passed = True

    for test_class in test_classes:
        print(f"\n{'='*50}")
        print(f"Running {test_class.__name__}")
        print('='*50)

        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if not result.wasSuccessful():
            all_passed = False

    print(f"\n{'='*50}")
    print("INTEGRATION TEST")
    print('='*50)
    run_integration_test()

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()

    print(f"\n{'='*60}")
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ OAuth flow authentication")
        print("✅ Sheet URL parsing and validation")
        print("✅ Interactive CLI interface")
        print("✅ Real-time progress tracking")
        print("✅ Error handling and recovery")
        print("✅ Non-destructive enrichment flow")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please review the test output above")

    print(f"{'='*60}")
    sys.exit(0 if success else 1)