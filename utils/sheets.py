"""
Google Sheets management utilities.

Handles authentication, reading, writing, and smart column management
for Google Sheets integration with proper error handling and batching.
"""

import asyncio
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

import gspread
from google.auth.exceptions import GoogleAuthError
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from .logging import get_logger

logger = get_logger(__name__)


class GoogleSheetsManager:
    """Manages Google Sheets operations with smart column detection."""

    # Google Sheets API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.readonly'
    ]

    def __init__(self, sheet_id: str, auth_mode: str = "oauth"):
        """Initialize Google Sheets manager.

        Args:
            sheet_id: Google Sheet ID
            auth_mode: Authentication mode ("oauth" or "service_account")
        """
        self.sheet_id = sheet_id
        self.auth_mode = auth_mode
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None

    async def authenticate(self) -> None:
        """Authenticate with Google Sheets API."""
        try:
            if self.auth_mode == "service_account":
                await self._authenticate_service_account()
            else:
                await self._authenticate_oauth()

            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            logger.info(f"Successfully connected to spreadsheet: {self.spreadsheet.title}")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    async def _authenticate_service_account(self) -> None:
        """Authenticate using service account credentials."""
        credentials_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH', './credentials.json')

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Service account credentials not found: {credentials_path}")

        try:
            credentials = ServiceAccountCredentials.from_service_account_file(
                credentials_path,
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(credentials)
            logger.info("Authenticated with service account")

        except Exception as e:
            raise GoogleAuthError(f"Service account authentication failed: {e}")

    async def _authenticate_oauth(self) -> None:
        """Authenticate using OAuth flow."""
        credentials_path = os.getenv('GOOGLE_OAUTH_CREDENTIALS_PATH', './credentials.json')
        token_path = './token.json'

        credentials = None

        # Try to load existing token
        if os.path.exists(token_path):
            try:
                credentials = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            except Exception as e:
                logger.debug(f"Could not load existing token: {e}")

        # If no valid credentials, run OAuth flow
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    logger.debug(f"Could not refresh token: {e}")
                    credentials = None

            if not credentials:
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(f"OAuth credentials not found: {credentials_path}")

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path,
                    self.SCOPES
                )
                credentials = flow.run_local_server(port=0)

                # Save credentials for next run
                with open(token_path, 'w') as token:
                    token.write(credentials.to_json())

        self.client = gspread.authorize(credentials)
        logger.info("Authenticated with OAuth")

    async def get_worksheet(self, worksheet_name: str) -> gspread.Worksheet:
        """Get worksheet by name.

        Args:
            worksheet_name: Name of the worksheet

        Returns:
            Worksheet object
        """
        if not self.spreadsheet:
            await self.authenticate()

        try:
            return self.spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            raise ValueError(f"Worksheet '{worksheet_name}' not found")

    async def get_headers(self, worksheet_name: str) -> List[str]:
        """Get header row from worksheet.

        Args:
            worksheet_name: Name of the worksheet

        Returns:
            List of header values
        """
        worksheet = await self.get_worksheet(worksheet_name)

        try:
            headers = worksheet.row_values(1)
            return headers
        except Exception as e:
            logger.error(f"Error getting headers: {e}")
            raise

    async def update_headers(self, worksheet_name: str, headers: List[str]) -> None:
        """Update header row in worksheet.

        Args:
            worksheet_name: Name of the worksheet
            headers: New header values
        """
        worksheet = await self.get_worksheet(worksheet_name)

        try:
            # Clear existing headers and set new ones
            range_name = f"1:{1}"
            worksheet.batch_clear([range_name])

            # Update with new headers
            if headers:
                worksheet.update(range_name, [headers])

            logger.info(f"Updated headers with {len(headers)} columns")

        except Exception as e:
            logger.error(f"Error updating headers: {e}")
            raise

    async def get_all_data(self, worksheet_name: str) -> List[List[str]]:
        """Get all data from worksheet.

        Args:
            worksheet_name: Name of the worksheet

        Returns:
            List of rows, each row is a list of cell values
        """
        worksheet = await self.get_worksheet(worksheet_name)

        try:
            # Get all values
            data = worksheet.get_all_values()
            return data

        except Exception as e:
            logger.error(f"Error getting all data: {e}")
            raise

    async def get_row_data(self, worksheet_name: str, row_number: int) -> List[str]:
        """Get data from specific row.

        Args:
            worksheet_name: Name of the worksheet
            row_number: Row number (1-based)

        Returns:
            List of cell values for the row
        """
        worksheet = await self.get_worksheet(worksheet_name)

        try:
            row_data = worksheet.row_values(row_number)
            return row_data

        except Exception as e:
            logger.error(f"Error getting row {row_number}: {e}")
            raise

    async def update_cells(
        self,
        worksheet_name: str,
        row_number: int,
        updates: Dict[int, str]
    ) -> None:
        """Update specific cells in a row.

        Args:
            worksheet_name: Name of the worksheet
            row_number: Row number (1-based)
            updates: Dictionary mapping column indices (1-based) to values
        """
        if not updates:
            return

        worksheet = await self.get_worksheet(worksheet_name)

        try:
            # Prepare batch update
            cells_to_update = []

            for col_index, value in updates.items():
                cell_address = self._get_cell_address(row_number, col_index)
                cells_to_update.append({
                    'range': cell_address,
                    'values': [[str(value)]]
                })

            # Batch update
            if cells_to_update:
                worksheet.batch_update(cells_to_update, value_input_option='USER_ENTERED')
                logger.debug(f"Updated {len(cells_to_update)} cells in row {row_number}")

        except Exception as e:
            logger.error(f"Error updating cells in row {row_number}: {e}")
            raise

    async def append_row(
        self,
        worksheet_name: str,
        values: List[str],
        value_input_option: str = 'USER_ENTERED'
    ) -> None:
        """Append a new row to worksheet.

        Args:
            worksheet_name: Name of the worksheet
            values: Values to append
            value_input_option: How to interpret input values
        """
        worksheet = await self.get_worksheet(worksheet_name)

        try:
            worksheet.append_row(values, value_input_option=value_input_option)
            logger.debug(f"Appended row with {len(values)} values")

        except Exception as e:
            logger.error(f"Error appending row: {e}")
            raise

    async def get_column_values(
        self,
        worksheet_name: str,
        column_index: int,
        start_row: int = 1
    ) -> List[str]:
        """Get all values from a specific column.

        Args:
            worksheet_name: Name of the worksheet
            column_index: Column index (1-based)
            start_row: Starting row (1-based)

        Returns:
            List of column values
        """
        worksheet = await self.get_worksheet(worksheet_name)

        try:
            column_letter = self._column_index_to_letter(column_index)
            range_name = f"{column_letter}{start_row}:{column_letter}"
            values = worksheet.get(range_name)

            # Flatten the result
            return [row[0] if row else '' for row in values]

        except Exception as e:
            logger.error(f"Error getting column {column_index} values: {e}")
            raise

    async def find_last_used_column(self, worksheet_name: str) -> int:
        """Find the last column with data.

        Args:
            worksheet_name: Name of the worksheet

        Returns:
            Last used column index (1-based)
        """
        headers = await self.get_headers(worksheet_name)

        # Find last non-empty header
        last_col = 0
        for i, header in enumerate(headers, 1):
            if header and header.strip():
                last_col = i

        return last_col

    async def find_managed_columns(
        self,
        worksheet_name: str,
        namespace: str = "ENRICH_"
    ) -> Dict[str, int]:
        """Find existing managed columns.

        Args:
            worksheet_name: Name of the worksheet
            namespace: Column namespace prefix

        Returns:
            Dictionary mapping header names to column indices
        """
        headers = await self.get_headers(worksheet_name)
        managed_columns = {}

        for i, header in enumerate(headers, 1):
            if header and header.startswith(namespace):
                managed_columns[header] = i

        return managed_columns

    def _get_cell_address(self, row: int, col: int) -> str:
        """Convert row and column numbers to cell address.

        Args:
            row: Row number (1-based)
            col: Column number (1-based)

        Returns:
            Cell address (e.g., "A1", "B2")
        """
        col_letter = self._column_index_to_letter(col)
        return f"{col_letter}{row}"

    def _column_index_to_letter(self, col_index: int) -> str:
        """Convert column index to letter(s).

        Args:
            col_index: Column index (1-based)

        Returns:
            Column letter(s) (e.g., "A", "B", "AA")
        """
        result = ""
        while col_index > 0:
            col_index -= 1
            result = chr(65 + (col_index % 26)) + result
            col_index //= 26
        return result

    async def batch_update_rows(
        self,
        worksheet_name: str,
        updates: Dict[int, Dict[int, str]]
    ) -> None:
        """Batch update multiple rows.

        Args:
            worksheet_name: Name of the worksheet
            updates: Dictionary mapping row numbers to column updates
        """
        if not updates:
            return

        worksheet = await self.get_worksheet(worksheet_name)

        try:
            # Prepare all cell updates
            all_updates = []

            for row_number, row_updates in updates.items():
                for col_index, value in row_updates.items():
                    cell_address = self._get_cell_address(row_number, col_index)
                    all_updates.append({
                        'range': cell_address,
                        'values': [[str(value)]]
                    })

            # Batch update all cells
            if all_updates:
                # Split into chunks to avoid API limits
                chunk_size = 100
                for i in range(0, len(all_updates), chunk_size):
                    chunk = all_updates[i:i + chunk_size]
                    worksheet.batch_update(chunk, value_input_option='USER_ENTERED')

                logger.info(f"Batch updated {len(all_updates)} cells")

        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            raise

    async def get_sheet_info(self) -> Dict[str, Any]:
        """Get spreadsheet information.

        Returns:
            Dictionary with spreadsheet metadata
        """
        if not self.spreadsheet:
            await self.authenticate()

        try:
            # Get basic info
            info = {
                'id': self.spreadsheet.id,
                'title': self.spreadsheet.title,
                'url': self.spreadsheet.url,
                'worksheets': []
            }

            # Get worksheet info
            for worksheet in self.spreadsheet.worksheets():
                ws_info = {
                    'title': worksheet.title,
                    'id': worksheet.id,
                    'row_count': worksheet.row_count,
                    'col_count': worksheet.col_count
                }
                info['worksheets'].append(ws_info)

            return info

        except Exception as e:
            logger.error(f"Error getting sheet info: {e}")
            raise