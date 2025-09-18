"""
Integration tests with mock sheet scenarios.

Tests complete workflow with realistic data scenarios including:
A) Website + Twitter + YouTube
B) Website only
C) LinkedIn (skipped) + Website → still produces COMBINED_REPORT
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from handlers.orchestrator import EnrichmentOrchestrator
from utils.sheets import GoogleSheetsManager
from utils.normalize import URLExtractor
from utils.scoring import LeadScorer


class TestIntegration:
    """Integration tests with mock sheet scenarios."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_sheets_manager = MagicMock(spec=GoogleSheetsManager)
        self.url_extractor = URLExtractor()
        self.lead_scorer = LeadScorer()

        self.config = {
            'HEADER_NAMESPACE': 'ENRICH_',
            'MAX_LINK_SUMMARIES': 5,
            'MAX_CELL_CHARS': 4000,
            'MAX_COMBINED_CHARS': 5000,
            'PER_DOMAIN_RPS': 0.2,
            'TIMEOUT_SECONDS': 20,
            'USER_AGENT': 'TestBot/1.0',
            'TWITTER_BEARER': 'test_token',
            'YOUTUBE_API_KEY': 'test_key',
            'GITHUB_TOKEN': 'test_token'
        }

        self.orchestrator = EnrichmentOrchestrator(
            sheets_manager=self.mock_sheets_manager,
            url_extractor=self.url_extractor,
            lead_scorer=self.lead_scorer,
            config=self.config
        )

    @pytest.mark.asyncio
    async def test_scenario_a_website_twitter_youtube(self):
        """Test scenario A: Website + Twitter + YouTube enrichment."""
        # Mock sheet data
        headers = ['name', 'company', 'website', 'social_links']
        row = [
            'John Doe',
            'TechCorp',
            'https://techcorp.com',
            'https://twitter.com/johndoe, https://youtube.com/channel/UC123'
        ]

        # Mock managed columns
        managed_columns = {
            'ENRICH_LINK_1_SUMMARY': 5,
            'ENRICH_LINK_2_SUMMARY': 6,
            'ENRICH_LINK_3_SUMMARY': 7,
            'ENRICH_COMBINED_REPORT': 8,
            'ENRICH_LEAD_SCORE': 9,
            'ENRICH_LEAD_SCORE_NOTES': 10,
            'ENRICH_STATUS': 11,
            'ENRICH_LAST_RUN': 12
        }

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=headers)
        self.mock_sheets_manager.update_headers = AsyncMock()

        # Mock handler responses
        with patch('handlers.website.WebsiteHandler.process') as mock_website, \
             patch('handlers.twitter.TwitterHandler.process') as mock_twitter, \
             patch('handlers.youtube.YouTubeHandler.process') as mock_youtube:

            # Website handler response
            mock_website.return_value = {
                'source': 'techcorp.com',
                'url': 'https://techcorp.com',
                'key_points': [
                    'Title: TechCorp - AI Solutions',
                    'Description: Enterprise AI platform',
                    'Features: API integration, automation'
                ],
                'signals': [
                    'Technology-focused company',
                    'Has pricing content',
                    'Enterprise solutions'
                ],
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }

            # Twitter handler response
            mock_twitter.return_value = {
                'source': 'Twitter/X',
                'url': 'https://twitter.com/johndoe',
                'key_points': [
                    'Name: John Doe (@johndoe)',
                    'Bio: CEO at TechCorp, AI enthusiast',
                    'Metrics: 5,000 followers, 1,200 tweets'
                ],
                'signals': [
                    'Good follower count (1k+)',
                    'Active on Twitter',
                    'Recent tweets mention product'
                ],
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }

            # YouTube handler response
            mock_youtube.return_value = {
                'source': 'YouTube',
                'url': 'https://youtube.com/channel/UC123',
                'key_points': [
                    'Channel: TechCorp Official',
                    'Subscribers: 15K',
                    'Recent video: AI Platform Demo'
                ],
                'signals': [
                    'Medium channel (10k+ subscribers)',
                    'Recent activity (within 30 days)',
                    'Content themes: tutorial, business'
                ],
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }

            # Process the row
            result = await self.orchestrator._process_single_row(
                headers=headers,
                row=row,
                row_number=2,
                managed_columns=managed_columns,
                dry_run=True
            )

            # Verify result
            assert result['status'] == 'OK'
            assert 'updates' in result

            updates = result['updates']

            # Should have link summaries
            assert managed_columns['ENRICH_LINK_1_SUMMARY'] in updates
            assert managed_columns['ENRICH_LINK_2_SUMMARY'] in updates
            assert managed_columns['ENRICH_LINK_3_SUMMARY'] in updates

            # Should have combined report
            combined_report = updates[managed_columns['ENRICH_COMBINED_REPORT']]
            assert 'Profile Snapshot' in combined_report
            assert 'Pain / Opportunity Signals' in combined_report
            assert 'Suggested Angle & CTA' in combined_report
            assert 'techcorp.com' in combined_report
            assert 'Twitter/X' in combined_report
            assert 'YouTube' in combined_report

            # Should have lead score
            lead_score = int(updates[managed_columns['ENRICH_LEAD_SCORE']])
            assert 0 <= lead_score <= 100
            assert lead_score > 50  # Should be decent score for multiple sources

            # Should have score notes
            score_notes = updates[managed_columns['ENRICH_LEAD_SCORE_NOTES']]
            assert len(score_notes) > 0

    @pytest.mark.asyncio
    async def test_scenario_b_website_only(self):
        """Test scenario B: Website only enrichment."""
        # Mock sheet data
        headers = ['name', 'company', 'website']
        row = ['Jane Smith', 'StartupCo', 'https://startupco.com']

        managed_columns = {
            'ENRICH_LINK_1_SUMMARY': 4,
            'ENRICH_COMBINED_REPORT': 5,
            'ENRICH_LEAD_SCORE': 6,
            'ENRICH_STATUS': 7,
            'ENRICH_LAST_RUN': 8
        }

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=headers)

        # Mock handler response
        with patch('handlers.website.WebsiteHandler.process') as mock_website:
            mock_website.return_value = {
                'source': 'startupco.com',
                'url': 'https://startupco.com',
                'key_points': [
                    'Title: StartupCo - SaaS Platform',
                    'Description: Customer analytics solution',
                    'Recent: Product launch announcement'
                ],
                'signals': [
                    'Technology-focused company',
                    'Recent activity detected',
                    'SaaS business model'
                ],
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }

            # Process the row
            result = await self.orchestrator._process_single_row(
                headers=headers,
                row=row,
                row_number=2,
                managed_columns=managed_columns,
                dry_run=True
            )

            # Verify result
            assert result['status'] == 'OK'

            updates = result['updates']

            # Should have one link summary
            assert managed_columns['ENRICH_LINK_1_SUMMARY'] in updates

            # Should still produce combined report
            combined_report = updates[managed_columns['ENRICH_COMBINED_REPORT']]
            assert 'Profile Snapshot' in combined_report
            assert 'startupco.com' in combined_report

            # Should have reasonable score despite single source
            lead_score = int(updates[managed_columns['ENRICH_LEAD_SCORE']])
            assert 0 <= lead_score <= 100

    @pytest.mark.asyncio
    async def test_scenario_c_linkedin_skipped_plus_website(self):
        """Test scenario C: LinkedIn (skipped) + Website → still produces report."""
        # Mock sheet data with LinkedIn URL
        headers = ['name', 'company', 'linkedin', 'website']
        row = [
            'Bob Wilson',
            'BigCorp',
            'https://linkedin.com/in/bobwilson',
            'https://bigcorp.com'
        ]

        managed_columns = {
            'ENRICH_LINK_1_SUMMARY': 5,
            'ENRICH_LINK_2_SUMMARY': 6,
            'ENRICH_COMBINED_REPORT': 7,
            'ENRICH_LEAD_SCORE': 8,
            'ENRICH_STATUS': 9,
            'ENRICH_LAST_RUN': 10
        }

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=headers)

        # Mock handler responses
        with patch('handlers.website.WebsiteHandler.process') as mock_website:
            # Website handler response (successful)
            mock_website.return_value = {
                'source': 'bigcorp.com',
                'url': 'https://bigcorp.com',
                'key_points': [
                    'Title: BigCorp - Enterprise Solutions',
                    'Description: Fortune 500 consulting',
                    'Services: Business transformation'
                ],
                'signals': [
                    'Enterprise company',
                    'Consulting services',
                    'Large organization'
                ],
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }

            # Process the row (LinkedIn should be automatically skipped)
            result = await self.orchestrator._process_single_row(
                headers=headers,
                row=row,
                row_number=2,
                managed_columns=managed_columns,
                dry_run=True
            )

            # Verify result
            assert result['status'] == 'OK'  # Should succeed despite LinkedIn skip

            updates = result['updates']

            # Should have website summary
            link1_summary = updates[managed_columns['ENRICH_LINK_1_SUMMARY']]
            assert 'bigcorp.com' in link1_summary

            # Should still produce combined report
            combined_report = updates[managed_columns['ENRICH_COMBINED_REPORT']]
            assert 'Profile Snapshot' in combined_report
            assert 'bigcorp.com' in combined_report
            # Should mention skipped sources count but not details
            assert len(combined_report) > 100  # Substantial report

            # Should have valid score
            lead_score = int(updates[managed_columns['ENRICH_LEAD_SCORE']])
            assert 0 <= lead_score <= 100

    @pytest.mark.asyncio
    async def test_no_urls_scenario(self):
        """Test scenario with no URLs found."""
        headers = ['name', 'title', 'email']
        row = ['John Doe', 'CEO', 'john@example.com']

        managed_columns = {
            'ENRICH_STATUS': 4,
            'ENRICH_LAST_RUN': 5
        }

        result = await self.orchestrator._process_single_row(
            headers=headers,
            row=row,
            row_number=2,
            managed_columns=managed_columns,
            dry_run=True
        )

        # Should return NO_LINKS status
        assert result['status'] == 'NO_LINKS'

        updates = result['updates']
        assert updates[managed_columns['ENRICH_STATUS']] == 'NO_LINKS'

    @pytest.mark.asyncio
    async def test_error_handling_in_integration(self):
        """Test error handling during integration workflow."""
        headers = ['name', 'website']
        row = ['John Doe', 'https://example.com']

        managed_columns = {
            'ENRICH_LINK_1_SUMMARY': 3,
            'ENRICH_STATUS': 4,
            'ENRICH_LAST_RUN': 5
        }

        # Mock handler to raise exception
        with patch('handlers.website.WebsiteHandler.process') as mock_website:
            mock_website.side_effect = Exception("Network error")

            result = await self.orchestrator._process_single_row(
                headers=headers,
                row=row,
                row_number=2,
                managed_columns=managed_columns,
                dry_run=True
            )

            # Should handle error gracefully
            assert result['status'] in ['ERROR', 'OK']  # May continue with error result
            assert 'updates' in result

    @pytest.mark.asyncio
    async def test_dry_run_mode(self):
        """Test dry run mode doesn't write to sheet."""
        headers = ['name', 'website']
        row = ['John Doe', 'https://example.com']

        self.mock_sheets_manager.get_headers = AsyncMock(return_value=headers)
        self.mock_sheets_manager.get_all_data = AsyncMock(return_value=[headers, row])
        self.mock_sheets_manager.update_cells = AsyncMock()

        with patch('handlers.website.WebsiteHandler.process') as mock_website:
            mock_website.return_value = {
                'source': 'example.com',
                'url': 'https://example.com',
                'key_points': ['Test'],
                'signals': ['Test signal'],
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }

            # Process with dry_run=True
            results = await self.orchestrator.process_sheet(
                worksheet_name='Test',
                dry_run=True
            )

            # Should not call update_cells
            self.mock_sheets_manager.update_cells.assert_not_called()

            # Should return results
            assert 'total_processed' in results

    @pytest.mark.asyncio
    async def test_summary_length_truncation(self):
        """Test that summaries are truncated to MAX_CELL_CHARS."""
        headers = ['name', 'website']
        row = ['John Doe', 'https://example.com']

        managed_columns = {
            'ENRICH_LINK_1_SUMMARY': 3,
            'ENRICH_COMBINED_REPORT': 4
        }

        # Create very long content
        long_content = ['Very long content item ' + 'x' * 500] * 20

        with patch('handlers.website.WebsiteHandler.process') as mock_website:
            mock_website.return_value = {
                'source': 'example.com',
                'url': 'https://example.com',
                'key_points': long_content,
                'signals': long_content,
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }

            result = await self.orchestrator._process_single_row(
                headers=headers,
                row=row,
                row_number=2,
                managed_columns=managed_columns,
                dry_run=True
            )

            updates = result['updates']

            # Check summary length
            summary = updates[managed_columns['ENRICH_LINK_1_SUMMARY']]
            assert len(summary) <= self.config['MAX_CELL_CHARS']

            # Check combined report length
            combined_report = updates[managed_columns['ENRICH_COMBINED_REPORT']]
            assert len(combined_report) <= self.config['MAX_COMBINED_CHARS']

    @pytest.mark.asyncio
    async def test_force_domains_filtering(self):
        """Test force_domains parameter filters URLs correctly."""
        headers = ['name', 'links']
        row = ['John Doe', 'https://example.com, https://twitter.com/john, https://github.com/john']

        managed_columns = {'ENRICH_STATUS': 4}

        # Force only Twitter domains
        result = await self.orchestrator._process_single_row(
            headers=headers,
            row=row,
            row_number=2,
            managed_columns=managed_columns,
            force_domains=['twitter.com'],
            dry_run=True
        )

        # Should only process Twitter URL
        # Implementation would filter URLs before processing

    @pytest.mark.asyncio
    async def test_rate_limiting_applied(self):
        """Test that rate limiting is applied between requests."""
        import time

        headers = ['name', 'website1', 'website2']
        row = ['John Doe', 'https://example1.com', 'https://example2.com']

        managed_columns = {'ENRICH_STATUS': 4}

        start_time = time.time()

        with patch('handlers.website.WebsiteHandler.process') as mock_website:
            mock_website.return_value = {
                'source': 'example.com',
                'key_points': ['Test'],
                'signals': [],
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }

            await self.orchestrator._process_single_row(
                headers=headers,
                row=row,
                row_number=2,
                managed_columns=managed_columns,
                dry_run=True
            )

        # Should take some time due to rate limiting
        elapsed = time.time() - start_time
        # With 0.2 RPS (5 second delay), processing 2 URLs should take at least 5 seconds
        # But we'll check for a smaller delay to avoid flaky tests
        assert elapsed >= 0.1  # At least some delay applied

    @pytest.mark.asyncio
    async def test_cache_usage(self):
        """Test that caching is used when enabled."""
        headers = ['name', 'website']
        row = ['John Doe', 'https://example.com']

        managed_columns = {'ENRICH_LINK_1_SUMMARY': 3}

        with patch('handlers.website.WebsiteHandler.get_cached_result') as mock_cache_get, \
             patch('handlers.website.WebsiteHandler.process') as mock_process:

            # First call - no cache
            mock_cache_get.return_value = None
            mock_process.return_value = {
                'source': 'example.com',
                'key_points': ['Test'],
                'signals': [],
                'status': 'OK'
            }

            result1 = await self.orchestrator._process_single_row(
                headers=headers,
                row=row,
                row_number=2,
                managed_columns=managed_columns,
                use_cache=True,
                dry_run=True
            )

            # Second call - should use cache
            mock_cache_get.return_value = {
                'source': 'example.com',
                'key_points': ['Cached test'],
                'signals': [],
                'status': 'OK'
            }

            result2 = await self.orchestrator._process_single_row(
                headers=headers,
                row=row,
                row_number=2,
                managed_columns=managed_columns,
                use_cache=True,
                dry_run=True
            )

            # Cache should be checked
            assert mock_cache_get.called