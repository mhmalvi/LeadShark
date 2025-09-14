#!/usr/bin/env python3
"""
Test Suite for Non-Destructive Enricher
Validates append-only behavior and data integrity
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))

from non_destructive_enricher import (
    NonDestructiveEnricher,
    EnrichmentResult,
    ENRICH_PREFIX,
    REQUIRED_ENRICH_HEADERS
)


class TestNonDestructiveEnricher(unittest.TestCase):
    """Test suite for non-destructive enrichment"""

    def setUp(self):
        """Setup test environment"""
        self.enricher = NonDestructiveEnricher("test_sheet_id", dry_run=True)
        self.mock_service = Mock()
        self.enricher.service = self.mock_service

    def test_header_append_preserves_existing(self):
        """Test: Headers are appended, existing ones preserved"""
        # Existing user headers
        existing_headers = [
            "Name", "Email", "Company", "LinkedIn URL",
            "Title", "Location", "Phone", "Notes"
        ]

        # Mock the service response
        self.mock_service.spreadsheets().values().get().execute.return_value = {
            'values': [existing_headers]
        }

        # Ensure enrichment headers
        enrich_cols = self.enricher.ensure_enrichment_headers(existing_headers)

        # Verify original headers unchanged
        self.assertEqual(existing_headers[:8], [
            "Name", "Email", "Company", "LinkedIn URL",
            "Title", "Location", "Phone", "Notes"
        ])

        # Verify enrichment columns would be appended
        self.assertTrue(all(
            col >= len(existing_headers)
            for col in enrich_cols.values()
        ))

        # Verify all required headers present
        for header in REQUIRED_ENRICH_HEADERS:
            self.assertIn(header, enrich_cols)

    def test_row_key_generation_priority(self):
        """Test: Row key generation follows priority order"""
        # Test 1: LinkedIn URL has highest priority
        row_data = {
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "email": "john@example.com",
            "name": "John Doe",
            "company": "Acme Corp"
        }
        key = self.enricher.get_row_key(row_data, 1)
        self.assertEqual(key, "linkedin:https://linkedin.com/in/johndoe")

        # Test 2: Email is second priority
        row_data = {
            "email": "jane@example.com",
            "name": "Jane Doe",
            "company": "Tech Corp"
        }
        key = self.enricher.get_row_key(row_data, 2)
        self.assertEqual(key, "email:jane@example.com")

        # Test 3: Company + Name is third priority
        row_data = {
            "name": "Bob Smith",
            "company": "StartupCo"
        }
        key = self.enricher.get_row_key(row_data, 3)
        self.assertEqual(key, "compound:StartupCo:Bob Smith")

        # Test 4: Existing row key is preserved
        row_data = {
            f"{ENRICH_PREFIX}Row Key": "existing:key:123",
            "email": "test@example.com"
        }
        key = self.enricher.get_row_key(row_data, 4)
        self.assertEqual(key, "existing:key:123")

    def test_row_matching_by_key(self):
        """Test: Rows are matched by key, not by position"""
        headers = ["Name", "Email", f"{ENRICH_PREFIX}Row Key"]
        sheet_data = [
            headers,
            ["John Doe", "john@example.com", "email:john@example.com"],
            ["Jane Smith", "jane@example.com", "email:jane@example.com"],
            ["Bob Johnson", "bob@example.com", "email:bob@example.com"]
        ]

        # Find row by key
        row_idx = self.enricher.find_row_by_key(
            "email:jane@example.com",
            sheet_data,
            headers
        )
        self.assertEqual(row_idx, 2)

        # Non-existent key returns None
        row_idx = self.enricher.find_row_by_key(
            "email:notfound@example.com",
            sheet_data,
            headers
        )
        self.assertIsNone(row_idx)

    def test_idempotency(self):
        """Test: Multiple runs only update enrichment columns"""
        enrichment_data_run1 = {
            f"{ENRICH_PREFIX}Primary URL": "https://example.com",
            f"{ENRICH_PREFIX}Page Title": "Example Site",
            f"{ENRICH_PREFIX}Confidence (0-100)": "75",
            f"{ENRICH_PREFIX}Last Enriched At (UTC)": "2024-01-01T10:00:00Z"
        }

        enrichment_data_run2 = {
            f"{ENRICH_PREFIX}Primary URL": "https://example.com",
            f"{ENRICH_PREFIX}Page Title": "Example Site - Updated",
            f"{ENRICH_PREFIX}Confidence (0-100)": "85",
            f"{ENRICH_PREFIX}Last Enriched At (UTC)": "2024-01-01T11:00:00Z"
        }

        # Map column indices
        self.enricher.enrich_columns = {
            f"{ENRICH_PREFIX}Primary URL": 10,
            f"{ENRICH_PREFIX}Page Title": 11,
            f"{ENRICH_PREFIX}Confidence (0-100)": 12,
            f"{ENRICH_PREFIX}Last Enriched At (UTC)": 13
        }

        # Simulate first run
        result1 = self.enricher.map_result_to_columns(EnrichmentResult(
            primary_url="https://example.com",
            page_title="Example Site",
            confidence=75
        ))

        # Simulate second run
        result2 = self.enricher.map_result_to_columns(EnrichmentResult(
            primary_url="https://example.com",
            page_title="Example Site - Updated",
            confidence=85
        ))

        # Verify only enrichment columns change
        self.assertNotEqual(
            result1[f"{ENRICH_PREFIX}Page Title"],
            result2[f"{ENRICH_PREFIX}Page Title"]
        )
        self.assertNotEqual(
            result1[f"{ENRICH_PREFIX}Confidence (0-100)"],
            result2[f"{ENRICH_PREFIX}Confidence (0-100)"]
        )

    def test_column_capacity_handling(self):
        """Test: Optional fields skipped when approaching column limit"""
        # Simulate near-capacity sheet (55 existing columns)
        existing_headers = [f"Column_{i}" for i in range(55)]

        self.enricher.total_columns = len(existing_headers)

        # Ensure enrichment headers with capacity check
        enrich_cols = self.enricher.ensure_enrichment_headers(existing_headers)

        # Verify we don't exceed MAX_COLUMNS
        total_cols = len(existing_headers) + len(enrich_cols)
        self.assertLessEqual(total_cols, 60)

        # Verify optional headers were skipped if necessary
        optional_headers = [
            f"{ENRICH_PREFIX}Employees (approx.)",
            f"{ENRICH_PREFIX}Revenue (approx.)",
            f"{ENRICH_PREFIX}Locations (|)",
            f"{ENRICH_PREFIX}Industry / Tags (|)",
            f"{ENRICH_PREFIX}Tech / Stack (|)"
        ]

        # Count how many optional headers were added
        optional_added = sum(1 for h in optional_headers if h in enrich_cols)

        # If we're near capacity, some optional headers should be skipped
        if len(existing_headers) >= 50:
            self.assertLess(optional_added, len(optional_headers))

    def test_error_handling_with_status(self):
        """Test: Errors are captured and status fields updated"""
        result = EnrichmentResult()

        # Simulate processing error
        try:
            raise ValueError("Simulated scraping error")
        except Exception as e:
            result.error = str(e)[:500]
            result.enrichment_status = "FAILED"
            result.scrape_status = "EMPTY"

        # Map to columns
        self.enricher.enrich_columns = {
            header: idx for idx, header in enumerate(REQUIRED_ENRICH_HEADERS)
        }
        mapped = self.enricher.map_result_to_columns(result)

        # Verify error fields
        self.assertEqual(mapped[f"{ENRICH_PREFIX}Error (last run)"], "Simulated scraping error")
        self.assertEqual(mapped[f"{ENRICH_PREFIX}Enrichment Status"], "FAILED")
        self.assertEqual(mapped[f"{ENRICH_PREFIX}Scrape Status"], "EMPTY")

    def test_data_normalization(self):
        """Test: Data is properly normalized and formatted"""
        result = EnrichmentResult(
            all_urls=["https://example.com", "https://example.org"],
            social_profiles=["twitter.com/example", "linkedin.com/company/example"],
            key_findings=["Finding 1", "Finding 2", "Finding 3"],
            contacts={
                'emails': ["info@example.com", "contact@example.com"],
                'phones': ["+1-555-0100", "+1-555-0200"]
            }
        )

        mapped = self.enricher.map_result_to_columns(result)

        # Verify pipe-delimited formatting
        self.assertEqual(
            mapped[f"{ENRICH_PREFIX}All URLs (|)"],
            "https://example.com|https://example.org"
        )
        self.assertEqual(
            mapped[f"{ENRICH_PREFIX}Social Profiles (|)"],
            "twitter.com/example|linkedin.com/company/example"
        )
        self.assertEqual(
            mapped[f"{ENRICH_PREFIX}Key Findings (| bullets)"],
            "Finding 1|Finding 2|Finding 3"
        )

        # Verify contacts formatting
        self.assertIn("info@example.com", mapped[f"{ENRICH_PREFIX}Contacts (emails|phones)"])
        self.assertIn("+1-555-0100", mapped[f"{ENRICH_PREFIX}Contacts (emails|phones)"])

    def test_truncation(self):
        """Test: Long fields are properly truncated"""
        # Create very long content
        long_text = "A" * 2000
        very_long_text = "B" * 25000

        result = EnrichmentResult(
            page_title=long_text,
            final_report=very_long_text
        )

        mapped = self.enricher.map_result_to_columns(result)

        # Verify truncation
        self.assertLessEqual(len(mapped[f"{ENRICH_PREFIX}Page Title"]), 1000)
        self.assertLessEqual(len(mapped[f"{ENRICH_PREFIX}Final Report (Markdown)"]), 20000)
        self.assertIn("[truncated]", mapped[f"{ENRICH_PREFIX}Final Report (Markdown)"])

    def test_version_constants(self):
        """Test: Version constants are properly set"""
        result = EnrichmentResult()
        mapped = self.enricher.map_result_to_columns(result)

        self.assertEqual(mapped[f"{ENRICH_PREFIX}Processor Version"], "v2.0")
        self.assertEqual(mapped[f"{ENRICH_PREFIX}Schema Version"], "S-Append-1.0")

    @patch('non_destructive_enricher.datetime')
    def test_timestamp_formatting(self, mock_datetime):
        """Test: Timestamps are in ISO-8601 UTC format"""
        mock_now = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        result = EnrichmentResult()
        mapped = self.enricher.map_result_to_columns(result)

        # Verify ISO-8601 format
        timestamp = mapped[f"{ENRICH_PREFIX}Last Enriched At (UTC)"]
        self.assertIn("2024-01-15", timestamp)
        self.assertIn("T", timestamp)  # ISO-8601 separator
        self.assertIn("Z", timestamp)  # UTC indicator

    def test_batch_update_request_structure(self):
        """Test: Batch update requests are properly structured"""
        self.enricher.enrich_columns = {
            f"{ENRICH_PREFIX}Row Key": 8,
            f"{ENRICH_PREFIX}Primary URL": 9,
            f"{ENRICH_PREFIX}Page Title": 10
        }

        enrichment_data = {
            f"{ENRICH_PREFIX}Primary URL": "https://test.com",
            f"{ENRICH_PREFIX}Page Title": "Test Page"
        }

        # Mock the batch update
        with patch.object(self.enricher, '_col_to_letter') as mock_col:
            mock_col.side_effect = lambda x: chr(65 + x)  # A, B, C...

            # Dry run to capture the request structure
            self.enricher.write_enrichment_data(
                row_index=5,
                row_key="test:key",
                enrichment_data=enrichment_data
            )

            # Verify column letter conversion was called correctly
            mock_col.assert_any_call(8)  # Row Key column
            mock_col.assert_any_call(9)  # Primary URL column
            mock_col.assert_any_call(10)  # Page Title column

    def test_dry_run_mode(self):
        """Test: Dry run mode doesn't make actual changes"""
        self.enricher.dry_run = True

        # Mock sheet data
        self.mock_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ["Name", "Email"],
                ["John Doe", "john@example.com"]
            ]
        }

        # Process sheet in dry run
        stats = self.enricher.process_sheet(max_rows=1)

        # Verify no actual updates were made
        self.mock_service.spreadsheets().values().update.assert_not_called()
        self.mock_service.spreadsheets().values().batchUpdate.assert_not_called()


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""

    def test_complete_enrichment_flow(self):
        """Test: Complete enrichment flow from start to finish"""
        enricher = NonDestructiveEnricher("test_sheet", dry_run=True)

        # Mock authentication
        with patch('non_destructive_enricher.authenticate_google_sheets'):
            enricher.authenticate()

        # Mock sheet data
        mock_service = Mock()
        enricher.service = mock_service

        mock_service.spreadsheets().values().get().execute.side_effect = [
            # First call: headers
            {'values': [["Name", "Email", "Company"]]},
            # Second call: full data
            {'values': [
                ["Name", "Email", "Company"],
                ["Alice", "alice@example.com", "TechCorp"],
                ["Bob", "bob@example.com", "StartupCo"]
            ]}
        ]

        # Process the sheet
        stats = enricher.process_sheet(max_rows=2)

        # Verify processing stats
        self.assertEqual(stats['rows_attempted'], 2)
        self.assertGreaterEqual(stats['elapsed_seconds'], 0)


def run_tests():
    """Run all tests with verbose output"""
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ All tests passed! Non-destructive enrichment is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
    sys.exit(0 if success else 1)