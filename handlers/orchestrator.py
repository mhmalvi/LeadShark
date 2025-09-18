"""
Enrichment orchestrator that coordinates all handlers and manages the
smart column detection and processing workflow.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .base import BaseHandler
from .website import WebsiteHandler
from .twitter import TwitterHandler
from .youtube import YouTubeHandler
from .github import GitHubHandler
from .news import NewsHandler
from utils.sheets import GoogleSheetsManager
from utils.normalize import URLExtractor
from utils.scoring import LeadScorer
from utils.cache import CacheManager
from utils.logging import get_logger

logger = get_logger(__name__)


class EnrichmentOrchestrator:
    """Coordinates the enrichment process across all handlers."""

    def __init__(
        self,
        sheets_manager: GoogleSheetsManager,
        url_extractor: URLExtractor,
        lead_scorer: LeadScorer,
        config: Dict[str, Any]
    ):
        """Initialize orchestrator.

        Args:
            sheets_manager: Google Sheets manager
            url_extractor: URL extraction utility
            lead_scorer: Lead scoring utility
            config: Configuration dictionary
        """
        self.sheets_manager = sheets_manager
        self.url_extractor = url_extractor
        self.lead_scorer = lead_scorer
        self.config = config

        # Initialize cache manager
        self.cache_manager = CacheManager(cache_dir="./.cache")

        # Initialize handlers
        self.handlers: List[BaseHandler] = [
            TwitterHandler(config, self.cache_manager),
            YouTubeHandler(config, self.cache_manager),
            GitHubHandler(config, self.cache_manager),
            NewsHandler(config, self.cache_manager),
            WebsiteHandler(config, self.cache_manager),  # Website handler last (fallback)
        ]

        # Managed column schema
        self.managed_headers = [
            'ENRICH_LINK_1_SUMMARY',
            'ENRICH_LINK_2_SUMMARY',
            'ENRICH_LINK_3_SUMMARY',
            'ENRICH_LINK_4_SUMMARY',
            'ENRICH_LINK_5_SUMMARY',
            'ENRICH_COMBINED_REPORT',
            'ENRICH_LEAD_SCORE',
            'ENRICH_LEAD_SCORE_NOTES',
            'ENRICH_STATUS',
            'ENRICH_LAST_RUN'
        ]

        # Rate limiting
        self.domain_last_request = {}
        self.per_domain_delay = 1.0 / config.get('PER_DOMAIN_RPS', 0.2)

    async def setup_managed_columns(
        self,
        worksheet_name: str,
        max_link_summaries: int = 5
    ) -> Dict[str, int]:
        """Setup managed column headers with smart detection.

        Args:
            worksheet_name: Name of worksheet
            max_link_summaries: Number of link summary columns

        Returns:
            Dictionary mapping header names to column indices
        """
        logger.info("Setting up managed column headers...")

        # Get current headers
        headers = await self.sheets_manager.get_headers(worksheet_name)
        if not headers:
            raise ValueError("Could not read worksheet headers")

        # Generate required headers based on max_link_summaries
        required_headers = []
        namespace = self.config.get('HEADER_NAMESPACE', 'ENRICH_')

        # Add link summary headers
        for i in range(1, max_link_summaries + 1):
            required_headers.append(f"{namespace}LINK_{i}_SUMMARY")

        # Add other managed headers
        required_headers.extend([
            f"{namespace}COMBINED_REPORT",
            f"{namespace}LEAD_SCORE",
            f"{namespace}LEAD_SCORE_NOTES",
            f"{namespace}STATUS",
            f"{namespace}LAST_RUN"
        ])

        # Find existing managed block
        managed_columns = {}
        managed_start_col = None

        for i, header in enumerate(headers, 1):
            if header and header.startswith(namespace):
                if managed_start_col is None:
                    managed_start_col = i
                managed_columns[header] = i

        # Determine what needs to be created
        missing_headers = []
        for header in required_headers:
            if header not in managed_columns:
                missing_headers.append(header)

        if missing_headers:
            if managed_start_col is None:
                # No managed block exists, create fresh block
                last_used_col = len([h for h in headers if h and h.strip()])
                insert_col = last_used_col + 1
                logger.info(f"Creating fresh managed block starting at column {insert_col}")
            else:
                # Extend existing managed block
                max_managed_col = max(managed_columns.values())
                insert_col = max_managed_col + 1
                logger.info(f"Extending managed block from column {insert_col}")

            # Add missing headers
            new_headers = headers.copy()
            for i, header in enumerate(missing_headers):
                col_index = insert_col + i
                # Ensure the list is long enough
                while len(new_headers) < col_index:
                    new_headers.append('')
                new_headers[col_index - 1] = header
                managed_columns[header] = col_index

            # Update headers in sheet
            await self.sheets_manager.update_headers(worksheet_name, new_headers)
            logger.info(f"Added {len(missing_headers)} new managed headers")

        # Return column mapping
        return managed_columns

    async def process_sheet(
        self,
        worksheet_name: str,
        row_range: Optional[Tuple[int, int]] = None,
        only_new: bool = False,
        force_domains: Optional[List[str]] = None,
        use_cache: bool = True,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Process the entire sheet with enrichment.

        Args:
            worksheet_name: Name of worksheet to process
            row_range: Optional row range to process (start, end)
            only_new: Only process rows with empty COMBINED_REPORT
            force_domains: Optional list of domains to restrict processing
            use_cache: Whether to use caching
            dry_run: Whether to preview without writing

        Returns:
            Processing results dictionary
        """
        logger.info("Starting sheet processing...")

        # Setup columns first
        managed_columns = await self.setup_managed_columns(worksheet_name)

        # Get all data
        all_data = await self.sheets_manager.get_all_data(worksheet_name)
        if not all_data:
            raise ValueError("Could not read sheet data")

        headers = all_data[0]
        data_rows = all_data[1:]

        # Determine rows to process
        start_row = row_range[0] if row_range else 2  # Row 2 (after headers)
        end_row = row_range[1] if row_range else len(data_rows) + 1

        # Adjust for 0-based indexing
        process_rows = data_rows[start_row - 2:end_row - 1]

        # Filter for only new rows if requested
        if only_new:
            combined_report_col = managed_columns.get('ENRICH_COMBINED_REPORT')
            if combined_report_col:
                filtered_rows = []
                for i, row in enumerate(process_rows):
                    # Check if combined report column is empty
                    if len(row) <= combined_report_col - 1 or not row[combined_report_col - 1].strip():
                        filtered_rows.append((start_row + i, row))
                process_rows = [row for _, row in filtered_rows]
                logger.info(f"Filtered to {len(process_rows)} rows with empty COMBINED_REPORT")

        if not process_rows:
            logger.info("No rows to process")
            return {'total_processed': 0, 'successful': 0, 'skipped_tos': 0, 'no_urls': 0, 'errors': 0}

        # Process rows
        results = {'total_processed': 0, 'successful': 0, 'skipped_tos': 0, 'no_urls': 0, 'errors': 0}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=logger.console if hasattr(logger, 'console') else None
        ) as progress:

            task = progress.add_task("Processing rows...", total=len(process_rows))

            for i, row in enumerate(process_rows):
                current_row_num = start_row + i
                progress.update(task, description=f"Processing row {current_row_num}")

                try:
                    # Process single row
                    row_result = await self._process_single_row(
                        headers=headers,
                        row=row,
                        row_number=current_row_num,
                        managed_columns=managed_columns,
                        force_domains=force_domains,
                        use_cache=use_cache,
                        dry_run=dry_run
                    )

                    # Update results
                    results['total_processed'] += 1
                    if row_result['status'] == 'OK':
                        results['successful'] += 1
                    elif row_result['status'] == 'SKIPPED_TOS':
                        results['skipped_tos'] += 1
                    elif row_result['status'] == 'NO_LINKS':
                        results['no_urls'] += 1
                    else:
                        results['errors'] += 1

                    # Write to sheet if not dry run
                    if not dry_run and row_result['updates']:
                        await self._write_row_updates(
                            worksheet_name=worksheet_name,
                            row_number=current_row_num,
                            updates=row_result['updates']
                        )

                    # Rate limiting between rows
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error processing row {current_row_num}: {e}")
                    results['errors'] += 1

                progress.advance(task)

        logger.info(f"Processing completed: {results}")
        return results

    async def _process_single_row(
        self,
        headers: List[str],
        row: List[str],
        row_number: int,
        managed_columns: Dict[str, int],
        force_domains: Optional[List[str]] = None,
        use_cache: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Process a single row.

        Args:
            headers: Sheet headers
            row: Row data
            row_number: Row number (1-based)
            managed_columns: Managed column mapping
            force_domains: Optional domain restrictions
            use_cache: Whether to use caching
            dry_run: Whether this is a dry run

        Returns:
            Processing result with updates
        """
        logger.debug(f"Processing row {row_number}")

        # Extract URLs from row
        urls = await self.url_extractor.extract_urls_from_row(headers, row)

        if not urls:
            return {
                'status': 'NO_LINKS',
                'updates': {
                    managed_columns.get('ENRICH_STATUS'): 'NO_LINKS',
                    managed_columns.get('ENRICH_LAST_RUN'): datetime.now(timezone.utc).isoformat()
                }
            }

        # Filter by force domains if specified
        if force_domains:
            filtered_urls = []
            for url in urls:
                domain = self._extract_domain(url)
                if any(force_domain in domain for force_domain in force_domains):
                    filtered_urls.append(url)
            urls = filtered_urls

            if not urls:
                return {
                    'status': 'NO_LINKS',
                    'updates': {
                        managed_columns.get('ENRICH_STATUS'): 'NO_LINKS',
                        managed_columns.get('ENRICH_LAST_RUN'): datetime.now(timezone.utc).isoformat()
                    }
                }

        # Process each URL
        url_results = []
        for url in urls:
            try:
                # Apply rate limiting
                await self._apply_rate_limiting(url)

                # Find handler
                handler = self._find_handler(url)
                if not handler:
                    logger.warning(f"No handler found for URL: {url}")
                    continue

                # Process URL
                result = await handler.process(url)
                url_results.append(result)

            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                # Add error result
                url_results.append({
                    'source': self._extract_domain(url),
                    'url': url,
                    'key_points': [f"Processing error: {str(e)}"],
                    'signals': [],
                    'status': 'ERROR',
                    'error': str(e),
                    'last_checked': datetime.now(timezone.utc).isoformat()
                })

        if not url_results:
            return {
                'status': 'ERROR',
                'updates': {
                    managed_columns.get('ENRICH_STATUS'): 'ERROR',
                    managed_columns.get('ENRICH_LAST_RUN'): datetime.now(timezone.utc).isoformat()
                }
            }

        # Generate updates
        updates = await self._generate_row_updates(
            url_results=url_results,
            managed_columns=managed_columns
        )

        # Determine overall status
        statuses = [result['status'] for result in url_results]
        if all(s == 'SKIPPED_TOS' for s in statuses):
            overall_status = 'SKIPPED_TOS'
        elif all(s == 'ERROR' for s in statuses):
            overall_status = 'ERROR'
        elif any(s == 'OK' for s in statuses):
            overall_status = 'OK'
        else:
            overall_status = 'ERROR'

        return {
            'status': overall_status,
            'updates': updates
        }

    async def _generate_row_updates(
        self,
        url_results: List[Dict[str, Any]],
        managed_columns: Dict[str, int]
    ) -> Dict[int, str]:
        """Generate updates for managed columns.

        Args:
            url_results: Results from URL processing
            managed_columns: Column mapping

        Returns:
            Dictionary mapping column indices to values
        """
        updates = {}

        # Per-link summaries
        max_summaries = self.config.get('MAX_LINK_SUMMARIES', 5)
        for i, result in enumerate(url_results[:max_summaries]):
            link_col = managed_columns.get(f"ENRICH_LINK_{i+1}_SUMMARY")
            if link_col:
                handler = self._find_handler(result['url'])
                if handler:
                    summary = handler.format_summary(result)
                    updates[link_col] = summary

        # Combined report
        combined_report = self._generate_combined_report(url_results)
        combined_col = managed_columns.get('ENRICH_COMBINED_REPORT')
        if combined_col:
            updates[combined_col] = combined_report

        # Lead score
        lead_score, score_notes = await self.lead_scorer.calculate_score(url_results)
        score_col = managed_columns.get('ENRICH_LEAD_SCORE')
        notes_col = managed_columns.get('ENRICH_LEAD_SCORE_NOTES')

        if score_col:
            updates[score_col] = str(lead_score)
        if notes_col:
            updates[notes_col] = score_notes

        # Status and timestamp
        status_col = managed_columns.get('ENRICH_STATUS')
        timestamp_col = managed_columns.get('ENRICH_LAST_RUN')

        if status_col:
            updates[status_col] = 'OK'
        if timestamp_col:
            updates[timestamp_col] = datetime.now(timezone.utc).isoformat()

        return updates

    def _generate_combined_report(self, url_results: List[Dict[str, Any]]) -> str:
        """Generate combined report from all URL results.

        Args:
            url_results: List of URL processing results

        Returns:
            Combined report string
        """
        lines = []

        # Profile snapshot
        lines.append("**Profile Snapshot:**")
        sources = set()
        key_insights = []

        for result in url_results:
            if result['status'] == 'OK':
                sources.add(result['source'])
                # Take first 2 key points from each source
                for point in result['key_points'][:2]:
                    if point and len(point.strip()) > 10:
                        key_insights.append(f"• {point}")

        lines.extend(key_insights[:4])  # Max 4 key insights
        lines.append("")

        # Pain/Opportunity signals
        lines.append("**Pain / Opportunity Signals:**")
        all_signals = []
        for result in url_results:
            if result['status'] == 'OK':
                all_signals.extend(result['signals'])

        unique_signals = list(dict.fromkeys(all_signals))  # Remove duplicates
        for signal in unique_signals[:6]:  # Max 6 signals
            lines.append(f"• {signal}")

        lines.append("")

        # Suggested angle & CTA
        lines.append("**Suggested Angle & CTA:**")
        lines.append("• Personalized outreach based on recent activity")
        lines.append("• Reference specific content or projects mentioned")
        if any('pricing' in s.lower() or 'contact' in s.lower() for s in all_signals):
            lines.append("• Sales-qualified lead - ready for direct outreach")

        lines.append("")

        # Data sources
        lines.append("**Data Sources:**")
        source_list = list(sources)
        if len(url_results) > len(source_list):
            extra_count = len(url_results) - len(source_list)
            source_list.append(f"(+{extra_count} more)")

        lines.append(", ".join(source_list))

        # Combine and truncate
        combined = "\n".join(lines)
        max_chars = self.config.get('MAX_COMBINED_CHARS', 5000)
        if len(combined) > max_chars:
            combined = combined[:max_chars - 3] + "..."

        return combined

    def _find_handler(self, url: str) -> Optional[BaseHandler]:
        """Find appropriate handler for URL.

        Args:
            url: URL to process

        Returns:
            Handler instance or None
        """
        for handler in self.handlers:
            if handler.can_handle(url):
                return handler
        return None

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: URL

        Returns:
            Domain string
        """
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except Exception:
            return 'unknown'

    async def _apply_rate_limiting(self, url: str) -> None:
        """Apply rate limiting per domain.

        Args:
            url: URL being processed
        """
        domain = self._extract_domain(url)
        now = asyncio.get_event_loop().time()

        if domain in self.domain_last_request:
            time_since_last = now - self.domain_last_request[domain]
            if time_since_last < self.per_domain_delay:
                sleep_time = self.per_domain_delay - time_since_last
                await asyncio.sleep(sleep_time)

        self.domain_last_request[domain] = now

    async def _write_row_updates(
        self,
        worksheet_name: str,
        row_number: int,
        updates: Dict[int, str]
    ) -> None:
        """Write updates to specific row.

        Args:
            worksheet_name: Worksheet name
            row_number: Row number (1-based)
            updates: Dictionary mapping column indices to values
        """
        if not updates:
            return

        try:
            await self.sheets_manager.update_cells(
                worksheet_name=worksheet_name,
                row_number=row_number,
                updates=updates
            )
        except Exception as e:
            logger.error(f"Error writing updates to row {row_number}: {e}")
            raise