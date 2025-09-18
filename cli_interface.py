#!/usr/bin/env python3
"""
🦈 LeadShark Enhanced CLI Interface with Rich Progress Bars and Interactive UX
Provides predatory command-line experience for lead enrichment operations
"""

import os
import sys
import time
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from google_sheets_auth import (
    parse_sheet_id_from_url,
    get_sheet_metadata,
    preview_sheet_data,
    validate_sheet_access
)


class CLIInterface:
    """🦈 LeadShark enhanced CLI interface with predatory formatting and interactive lead hunting features"""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.use_rich = RICH_AVAILABLE

        # Progress tracking
        self.current_progress = None
        self.overall_task = None
        self.row_task = None

        # Stats
        self.stats = {
            'ok': 0,
            'partial': 0,
            'failed': 0,
            'skipped': 0
        }

    def print_banner(self):
        """Display application banner"""
        if self.use_rich:
            banner = Panel.fit(
                "[bold red]>> LeadShark - Predatory Lead Enrichment <<[/bold red]\n"
                "[dim]Interactive • Non-Destructive • Real-Time Hunt Progress[/dim]\n\n"
                "+ [green]Append-only lead enrichment[/green] preserves all original prospect data\n"
                "* [blue]OAuth2 authentication[/blue] with scope verification\n"
                "~ [yellow]Live progress tracking[/yellow] with detailed status\n"
                "# [magenta]Smart column management[/magenta] under 60-column limit",
                box=box.DOUBLE,
                border_style="blue"
            )
            self.console.print(banner)
        else:
            print("="*70)
            print("    >> LeadShark - Predatory Lead Enrichment <<")
            print("    Interactive • Non-Destructive • Real-Time Hunt Progress")
            print("="*70)

    def print_error(self, message: str, details: Optional[List[str]] = None):
        """Print formatted error message"""
        if self.use_rich:
            panel = Panel(
                f"[bold red]{message}[/bold red]" +
                (f"\n\n[dim]{chr(10).join(details)}[/dim]" if details else ""),
                title="[X] Error",
                border_style="red"
            )
            self.console.print(panel)
        else:
            print(f"\n[X] Error: {message}")
            if details:
                for detail in details:
                    print(f"   {detail}")

    def print_warning(self, message: str):
        """Print formatted warning message"""
        if self.use_rich:
            self.console.print(f"[bold yellow][!] {message}[/bold yellow]")
        else:
            print(f"[!] Warning: {message}")

    def print_success(self, message: str):
        """Print formatted success message"""
        if self.use_rich:
            self.console.print(f"[bold green][OK] {message}[/bold green]")
        else:
            print(f"[OK] {message}")

    def print_info(self, message: str):
        """Print formatted info message"""
        if self.use_rich:
            self.console.print(f"[blue][i] {message}[/blue]")
        else:
            print(f"[i] {message}")

    def prompt_sheet_input(self) -> Optional[str]:
        """Prompt user for Google Sheet URL or ID"""
        if self.use_rich:
            self.console.print("\n[bold cyan][+] Sheet Selection[/bold cyan]")
            return Prompt.ask(
                "[green]Paste your Google Sheet link or ID[/green]",
                default="",
                show_default=False
            )
        else:
            print("\n[+] Sheet Selection")
            return input("Paste your Google Sheet link or ID: ").strip()

    def select_worksheet(self, metadata: Dict) -> Optional[str]:
        """Let user select worksheet/tab from available options"""
        sheets = metadata.get('sheets', [])

        if len(sheets) == 1:
            sheet_name = sheets[0]['title']
            if self.use_rich:
                self.console.print(f"[green]Using worksheet:[/green] {sheet_name}")
            else:
                print(f"Using worksheet: {sheet_name}")
            return sheet_name

        # Display worksheet options
        if self.use_rich:
            table = Table(title="Available Worksheets", box=box.SIMPLE)
            table.add_column("#", style="cyan", width=3)
            table.add_column("Name", style="green")
            table.add_column("Rows", style="yellow", justify="right")
            table.add_column("Columns", style="blue", justify="right")

            for i, sheet in enumerate(sheets, 1):
                table.add_row(
                    str(i),
                    sheet['title'],
                    str(sheet.get('rowCount', '?')),
                    str(sheet.get('columnCount', '?'))
                )

            self.console.print(table)

            # Prompt for selection
            choice = IntPrompt.ask(
                f"[cyan]Select worksheet (1-{len(sheets)})[/cyan]",
                default=1,
                show_default=True
            )
        else:
            print("\nAvailable Worksheets:")
            for i, sheet in enumerate(sheets, 1):
                print(f"  {i}. {sheet['title']} ({sheet.get('rowCount', '?')} rows, {sheet.get('columnCount', '?')} cols)")

            while True:
                try:
                    choice = input(f"Select worksheet (1-{len(sheets)}) [1]: ").strip()
                    choice = int(choice) if choice else 1
                    break
                except ValueError:
                    print("Please enter a valid number")

        if 1 <= choice <= len(sheets):
            return sheets[choice - 1]['title']
        else:
            self.print_error("Invalid selection")
            return None

    def show_sheet_preview(self, preview_data: Dict) -> bool:
        """Show sheet preview and ask for confirmation"""
        headers = preview_data.get('headers', [])
        preview_rows = preview_data.get('preview_rows', [])
        total_rows = preview_data.get('total_rows', 0)
        sheet_name = preview_data.get('sheet_name', 'Unknown')

        if self.use_rich:
            # Create preview table
            table = Table(title=f"Preview: {sheet_name}", box=box.SIMPLE_HEAD)

            # Add header columns (limit to first 8 for display)
            for header in headers[:8]:
                table.add_column(header[:15] + "..." if len(header) > 15 else header, style="cyan")

            # Add preview rows
            for row in preview_rows[:3]:
                display_row = []
                for i, cell in enumerate(row[:8]):
                    if i >= len(headers):
                        break
                    cell_str = str(cell)[:20] + "..." if len(str(cell)) > 20 else str(cell)
                    display_row.append(cell_str)

                # Pad with empty cells if needed
                while len(display_row) < min(8, len(headers)):
                    display_row.append("")

                table.add_row(*display_row)

            self.console.print(table)

            # Show summary
            info_text = f"[bold]Total data rows:[/bold] {total_rows}\n"
            info_text += f"[bold]Total columns:[/bold] {len(headers)}\n"
            info_text += f"[bold]Worksheet:[/bold] {sheet_name}"

            panel = Panel(info_text, title="[~] Sheet Summary", border_style="blue")
            self.console.print(panel)

            return Confirm.ask("[green]Proceed with this sheet?[/green]", default=True)
        else:
            print(f"\n[~] Preview: {sheet_name}")
            print(f"Headers: {', '.join(headers[:5])}" + ("..." if len(headers) > 5 else ""))
            print(f"Total data rows: {total_rows}")
            print(f"Total columns: {len(headers)}")

            if preview_rows:
                print(f"Sample row: {preview_rows[0][:3]}" + ("..." if len(preview_rows[0]) > 3 else ""))

            response = input("Proceed with this sheet? (Y/n): ").strip().lower()
            return response != 'n'

    def prompt_processing_mode(self) -> Dict[str, Any]:
        """Prompt user for processing mode and parameters"""
        if self.use_rich:
            self.console.print("\n[bold cyan][+] Processing Options[/bold cyan]")

            # Mode selection
            mode_table = Table(box=box.SIMPLE)
            mode_table.add_column("Mode", style="green")
            mode_table.add_column("Description", style="white")

            mode_table.add_row("1", "Test run (first 5 rows)")
            mode_table.add_row("2", "Custom row count")
            mode_table.add_row("3", "Process all rows")
            mode_table.add_row("4", "Dry run (preview only)")

            self.console.print(mode_table)

            mode = IntPrompt.ask("Select processing mode", default=1, show_default=True)

            options = {
                'dry_run': False,
                'max_rows': None,
                'start_row': 2,
                'all_rows': False
            }

            if mode == 1:  # Test run
                options['max_rows'] = 5
            elif mode == 2:  # Custom count
                options['max_rows'] = IntPrompt.ask("How many rows to process?", default=10)
            elif mode == 3:  # All rows
                options['all_rows'] = True
            elif mode == 4:  # Dry run
                options['dry_run'] = True
                options['max_rows'] = IntPrompt.ask("Preview how many rows?", default=3)

            # Rate limiting profile
            rate_profile = Prompt.ask(
                "Rate limiting profile",
                choices=["default", "slow"],
                default="default"
            )
            options['rate_profile'] = rate_profile

            return options
        else:
            print("\n[+] Processing Options:")
            print("1. Test run (first 5 rows)")
            print("2. Custom row count")
            print("3. Process all rows")
            print("4. Dry run (preview only)")

            while True:
                try:
                    mode = input("Select mode (1-4) [1]: ").strip()
                    mode = int(mode) if mode else 1
                    break
                except ValueError:
                    print("Please enter 1, 2, 3, or 4")

            options = {'dry_run': False, 'max_rows': None, 'all_rows': False}

            if mode == 1:
                options['max_rows'] = 5
            elif mode == 2:
                while True:
                    try:
                        options['max_rows'] = int(input("How many rows to process? "))
                        break
                    except ValueError:
                        print("Please enter a number")
            elif mode == 3:
                options['all_rows'] = True
            elif mode == 4:
                options['dry_run'] = True
                options['max_rows'] = 3

            return options

    def create_progress_display(self, total_rows: int, mode: str, sheet_name: str, dry_run: bool = False):
        """Create rich progress display"""
        if not self.use_rich:
            return None

        # Create progress bars
        self.current_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
            transient=False
        )

        # Add overall progress task
        self.overall_task = self.current_progress.add_task(
            f"[green]Processing {sheet_name} ({mode}{'• DRY RUN' if dry_run else ''})",
            total=total_rows
        )

        # Add current row task
        self.row_task = self.current_progress.add_task(
            "[cyan]Ready to start...",
            total=100
        )

        return self.current_progress

    def update_progress(self, row_index: int, row_name: str, status: str, details: str = ""):
        """Update progress display with current row information"""
        if self.use_rich and self.current_progress:
            # Update overall progress
            self.current_progress.update(self.overall_task, advance=1)

            # Status emoji mapping
            status_emoji = {
                'processing': '[~]',
                'ok': '[OK]',
                'partial': '[!]',
                'failed': '[X]',
                'skipped': '[>]'
            }

            emoji = status_emoji.get(status.lower(), '•')

            # Update current row
            description = f"[cyan]#{row_index} {row_name[:20]} — {emoji} {status.upper()}"
            if details:
                description += f" | {details}"

            self.current_progress.update(
                self.row_task,
                description=description,
                completed=100 if status != 'processing' else 50
            )

            # Update stats
            if status.lower() in self.stats:
                self.stats[status.lower()] += 1
        else:
            # Fallback for non-rich terminals
            status_symbol = {'ok': '[OK]', 'partial': '[!]', 'failed': '[X]', 'skipped': '[>]'}.get(status.lower(), '*')
            print(f"#{row_index} {row_name[:30]:<30} {status_symbol} {status.upper()} | {details}")

    def show_final_summary(self, stats: Dict[str, Any], elapsed_time: float):
        """Display final processing summary"""
        if self.use_rich:
            # Create summary table
            summary_table = Table(title="[~] Processing Summary", box=box.DOUBLE)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Count", style="bold white", justify="right")
            summary_table.add_column("Percentage", style="green", justify="right")

            total = sum([stats.get('ok', 0), stats.get('partial', 0), stats.get('failed', 0), stats.get('skipped', 0)])

            if total > 0:
                summary_table.add_row("[OK] Successful", str(stats.get('ok', 0)), f"{stats.get('ok', 0)/total*100:.1f}%")
                summary_table.add_row("[!] Partial", str(stats.get('partial', 0)), f"{stats.get('partial', 0)/total*100:.1f}%")
                summary_table.add_row("[X] Failed", str(stats.get('failed', 0)), f"{stats.get('failed', 0)/total*100:.1f}%")
                summary_table.add_row("[>] Skipped", str(stats.get('skipped', 0)), f"{stats.get('skipped', 0)/total*100:.1f}%")
                summary_table.add_row("", "", "")
                summary_table.add_row("[-] Total", str(total), "100.0%")

            self.console.print(summary_table)

            # Performance metrics
            if total > 0:
                perf_text = f"[bold]Processing Time:[/bold] {elapsed_time:.1f} seconds\n"
                perf_text += f"[bold]Average per Row:[/bold] {elapsed_time/total:.2f} seconds\n"
                perf_text += f"[bold]Success Rate:[/bold] {(stats.get('ok', 0) + stats.get('partial', 0))/total*100:.1f}%"

                panel = Panel(perf_text, title="⚡ Performance", border_style="green")
                self.console.print(panel)
        else:
            print("\n" + "="*60)
            print("[~] PROCESSING SUMMARY")
            print("="*60)
            total = sum([stats.get('ok', 0), stats.get('partial', 0), stats.get('failed', 0), stats.get('skipped', 0)])

            print(f"[OK] Successful: {stats.get('ok', 0)}")
            print(f"[!] Partial: {stats.get('partial', 0)}")
            print(f"[X] Failed: {stats.get('failed', 0)}")
            print(f"[>] Skipped: {stats.get('skipped', 0)}")
            print(f"[-] Total: {total}")
            print(f"[T] Time: {elapsed_time:.1f}s ({elapsed_time/total:.2f}s per row)" if total > 0 else "")

    def start_progress(self):
        """Start the progress display"""
        if self.use_rich and self.current_progress:
            self.current_progress.start()

    def stop_progress(self):
        """Stop the progress display"""
        if self.use_rich and self.current_progress:
            self.current_progress.stop()

    def get_console(self):
        """Get the rich console instance"""
        return self.console if self.use_rich else None


def install_rich_hint():
    """Show hint about installing rich for better experience"""
    print("💡 For a better experience, install rich:")
    print("   pip install rich")
    print()


# Usage example and testing
if __name__ == "__main__":
    cli = CLIInterface()

    if not RICH_AVAILABLE:
        install_rich_hint()

    # Test the interface
    cli.print_banner()

    # Test sheet input
    sheet_input = cli.prompt_sheet_input()
    if sheet_input:
        sheet_id = parse_sheet_id_from_url(sheet_input)
        print(f"Parsed Sheet ID: {sheet_id}")

    # Test mode selection
    options = cli.prompt_processing_mode()
    print(f"Selected options: {options}")

    # Test progress (simulation)
    if RICH_AVAILABLE:
        progress = cli.create_progress_display(5, "Test", "Sample Sheet")

        with progress:
            for i in range(1, 6):
                cli.update_progress(i, f"Person {i}", "processing", "Scraping...")
                time.sleep(1)
                cli.update_progress(i, f"Person {i}", "ok", "3 sources, 85% confidence")
                time.sleep(0.5)

        cli.show_final_summary({'ok': 4, 'partial': 1, 'failed': 0, 'skipped': 0}, 12.5)