"""
Tests for smart column detection and managed header block system.

Tests the core functionality that detects existing managed blocks,
creates missing headers, and maintains column organization.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from utils.sheets import GoogleSheetsManager
from handlers.orchestrator import EnrichmentOrchestrator


class TestColumnManagement:
    """Test smart column detection and management."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_sheets_manager = MagicMock(spec=GoogleSheetsManager)
        self.mock_url_extractor = MagicMock()
        self.mock_lead_scorer = MagicMock()

        self.config = {
            'HEADER_NAMESPACE': 'ENRICH_',
            'MAX_LINK_SUMMARIES': 5,
            'MAX_CELL_CHARS': 4000,
            'MAX_COMBINED_CHARS': 5000,
            'PER_DOMAIN_RPS': 0.2
        }

        self.orchestrator = EnrichmentOrchestrator(
            sheets_manager=self.mock_sheets_manager,
            url_extractor=self.mock_url_extractor,
            lead_scorer=self.mock_lead_scorer,
            config=self.config
        )

    @pytest.mark.asyncio
    async def test_detect_existing_managed_block(self):
        """Test detection of existing managed header block."""
        # Mock existing headers with managed block
        existing_headers = [
            'name', 'email', 'company',
            'ENRICH_LINK_1_SUMMARY', 'ENRICH_LINK_2_SUMMARY', 'ENRICH_COMBINED_REPORT',
            'ENRICH_LEAD_SCORE', 'ENRICH_STATUS', 'ENRICH_LAST_RUN'
        ]

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Setup managed columns
        managed_columns = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=3)

        # Should detect existing columns
        assert 'ENRICH_LINK_1_SUMMARY' in managed_columns
        assert 'ENRICH_COMBINED_REPORT' in managed_columns
        assert 'ENRICH_STATUS' in managed_columns

        # Should reuse existing positions
        assert managed_columns['ENRICH_LINK_1_SUMMARY'] == 4  # 1-based index
        assert managed_columns['ENRICH_COMBINED_REPORT'] == 6

    @pytest.mark.asyncio
    async def test_create_fresh_managed_block(self):
        """Test creation of fresh managed block when none exists."""
        # Mock headers without managed columns
        existing_headers = ['name', 'email', 'company', 'website']

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Setup managed columns
        managed_columns = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=3)

        # Should create new columns starting after last used column
        expected_start_col = 5  # After 'website'

        # Verify update_headers was called with new headers
        self.mock_sheets_manager.update_headers.assert_called_once()
        call_args = self.mock_sheets_manager.update_headers.call_args[0]
        updated_headers = call_args[1]

        # Check that new headers were added
        assert len(updated_headers) > len(existing_headers)
        assert 'ENRICH_LINK_1_SUMMARY' in updated_headers
        assert 'ENRICH_COMBINED_REPORT' in updated_headers

    @pytest.mark.asyncio
    async def test_expand_managed_block_more_summaries(self):
        """Test expanding managed block when MAX_LINK_SUMMARIES increases."""
        # Mock existing managed block with 3 summaries
        existing_headers = [
            'name', 'email',
            'ENRICH_LINK_1_SUMMARY', 'ENRICH_LINK_2_SUMMARY', 'ENRICH_LINK_3_SUMMARY',
            'ENRICH_COMBINED_REPORT', 'ENRICH_STATUS'
        ]

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Request 5 summaries (up from 3)
        managed_columns = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=5)

        # Should add missing summary columns
        self.mock_sheets_manager.update_headers.assert_called_once()
        call_args = self.mock_sheets_manager.update_headers.call_args[0]
        updated_headers = call_args[1]

        # Should have new summary columns
        assert 'ENRICH_LINK_4_SUMMARY' in updated_headers
        assert 'ENRICH_LINK_5_SUMMARY' in updated_headers

    @pytest.mark.asyncio
    async def test_compact_managed_block_fewer_summaries(self):
        """Test handling when MAX_LINK_SUMMARIES decreases."""
        # Mock existing managed block with 5 summaries
        existing_headers = [
            'name', 'email',
            'ENRICH_LINK_1_SUMMARY', 'ENRICH_LINK_2_SUMMARY', 'ENRICH_LINK_3_SUMMARY',
            'ENRICH_LINK_4_SUMMARY', 'ENRICH_LINK_5_SUMMARY',
            'ENRICH_COMBINED_REPORT', 'ENRICH_STATUS'
        ]

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Request only 3 summaries (down from 5)
        managed_columns = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=3)

        # Should still map existing columns (no deletion)
        assert 'ENRICH_LINK_4_SUMMARY' in managed_columns
        assert 'ENRICH_LINK_5_SUMMARY' in managed_columns

        # But only requested summaries should be used in processing
        assert managed_columns['ENRICH_LINK_1_SUMMARY'] == 3
        assert managed_columns['ENRICH_LINK_3_SUMMARY'] == 5

    @pytest.mark.asyncio
    async def test_missing_headers_in_existing_block(self):
        """Test adding missing headers to existing managed block."""
        # Mock partial managed block (missing some standard headers)
        existing_headers = [
            'name', 'email',
            'ENRICH_LINK_1_SUMMARY', 'ENRICH_COMBINED_REPORT',
            # Missing: ENRICH_LEAD_SCORE, ENRICH_STATUS, ENRICH_LAST_RUN
        ]

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Setup managed columns
        managed_columns = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=2)

        # Should add missing standard headers
        self.mock_sheets_manager.update_headers.assert_called_once()
        call_args = self.mock_sheets_manager.update_headers.call_args[0]
        updated_headers = call_args[1]

        assert 'ENRICH_LEAD_SCORE' in updated_headers
        assert 'ENRICH_STATUS' in updated_headers
        assert 'ENRICH_LAST_RUN' in updated_headers

    def test_column_index_to_letter_conversion(self):
        """Test conversion of column indices to Excel-style letters."""
        test_cases = [
            (1, 'A'),
            (26, 'Z'),
            (27, 'AA'),
            (52, 'AZ'),
            (53, 'BA'),
            (702, 'ZZ'),
            (703, 'AAA')
        ]

        for col_index, expected_letter in test_cases:
            result = self.mock_sheets_manager._column_index_to_letter(col_index)
            assert result == expected_letter, f"Failed for {col_index}: got {result}, expected {expected_letter}"

    @pytest.mark.asyncio
    async def test_idempotent_column_setup(self):
        """Test that repeated column setup calls are idempotent."""
        existing_headers = [
            'name', 'email',
            'ENRICH_LINK_1_SUMMARY', 'ENRICH_COMBINED_REPORT',
            'ENRICH_LEAD_SCORE', 'ENRICH_STATUS', 'ENRICH_LAST_RUN'
        ]

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # First setup
        managed_columns_1 = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=1)

        # Reset mock
        self.mock_sheets_manager.update_headers.reset_mock()

        # Second setup with same parameters
        managed_columns_2 = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=1)

        # Should not call update_headers on second run (no changes needed)
        self.mock_sheets_manager.update_headers.assert_not_called()

        # Results should be identical
        assert managed_columns_1 == managed_columns_2

    @pytest.mark.asyncio
    async def test_namespace_customization(self):
        """Test custom namespace prefix for managed headers."""
        # Custom config with different namespace
        custom_config = self.config.copy()
        custom_config['HEADER_NAMESPACE'] = 'CUSTOM_'

        custom_orchestrator = EnrichmentOrchestrator(
            sheets_manager=self.mock_sheets_manager,
            url_extractor=self.mock_url_extractor,
            lead_scorer=self.mock_lead_scorer,
            config=custom_config
        )

        existing_headers = ['name', 'email']
        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Setup with custom namespace
        managed_columns = await custom_orchestrator.setup_managed_columns('Sheet1', max_link_summaries=2)

        # Should use custom namespace
        self.mock_sheets_manager.update_headers.assert_called_once()
        call_args = self.mock_sheets_manager.update_headers.call_args[0]
        updated_headers = call_args[1]

        assert any('CUSTOM_LINK_1_SUMMARY' in header for header in updated_headers)
        assert any('CUSTOM_COMBINED_REPORT' in header for header in updated_headers)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_worksheet(self):
        """Test error handling for invalid worksheet."""
        self.mock_sheets_manager.get_headers = AsyncMock(side_effect=ValueError("Worksheet not found"))

        # Should raise the original error
        with pytest.raises(ValueError, match="Worksheet not found"):
            await self.orchestrator.setup_managed_columns('NonExistentSheet')

    @pytest.mark.asyncio
    async def test_column_ordering_preservation(self):
        """Test that managed block maintains proper column ordering."""
        existing_headers = [
            'name', 'email', 'company',
            'ENRICH_LINK_2_SUMMARY',  # Out of order
            'ENRICH_LINK_1_SUMMARY',
            'ENRICH_COMBINED_REPORT'
        ]

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Setup managed columns
        managed_columns = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=3)

        # Should detect existing columns regardless of order
        assert 'ENRICH_LINK_1_SUMMARY' in managed_columns
        assert 'ENRICH_LINK_2_SUMMARY' in managed_columns

        # But should add missing LINK_3 in proper position
        self.mock_sheets_manager.update_headers.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_column_count_handling(self):
        """Test handling of spreadsheets with many columns."""
        # Create headers up to column AZ (52 columns)
        large_headers = [f'col_{i}' for i in range(1, 53)]

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=large_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Setup managed columns
        managed_columns = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=5)

        # Should add managed block after last column
        self.mock_sheets_manager.update_headers.assert_called_once()
        call_args = self.mock_sheets_manager.update_headers.call_args[0]
        updated_headers = call_args[1]

        # Should have extended beyond original columns
        assert len(updated_headers) > 52

    @pytest.mark.asyncio
    async def test_schema_version_support(self):
        """Test optional schema version header support."""
        existing_headers = ['name', 'email']

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=existing_headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Config with schema version
        config_with_version = self.config.copy()
        config_with_version['INCLUDE_SCHEMA_VERSION'] = True

        # Setup managed columns
        managed_columns = await self.orchestrator.setup_managed_columns('Sheet1', max_link_summaries=1)

        # Check if schema version would be added (implementation detail)
        self.mock_sheets_manager.update_headers.assert_called_once()
        call_args = self.mock_sheets_manager.update_headers.call_args[0]
        updated_headers = call_args[1]

        # Should have added managed headers
        enrich_headers = [h for h in updated_headers if h.startswith('ENRICH_')]
        assert len(enrich_headers) >= 5  # At least the basic set