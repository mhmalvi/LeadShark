#!/usr/bin/env python3
"""
Link Intelligence Orchestrator CLI
Interactive command-line interface for running the Link Intelligence Orchestrator.
"""

import sys
import os
import json
from datetime import datetime
import argparse
from typing import Dict, Any

sys.path.append(os.path.dirname(__file__))

from link_intelligence_orchestrator import LinkIntelligenceOrchestrator


def print_banner():
    """Print the CLI banner."""
    print("""
==================================================================
           LINK INTELLIGENCE ORCHESTRATOR v1.0
         Comprehensive Link Analysis & Lead Scoring
==================================================================
    """)


def get_user_input(prompt: str, default: Any = None, value_type: type = str) -> Any:
    """
    Get user input with optional default value.

    Args:
        prompt: Input prompt
        default: Default value
        value_type: Expected type

    Returns:
        User input or default
    """
    if default is not None:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    user_input = input(prompt).strip()

    if not user_input and default is not None:
        return default

    if value_type == bool:
        return user_input.lower() in ['yes', 'y', 'true', '1', 'on']
    elif value_type == int:
        return int(user_input) if user_input else default
    else:
        return user_input


def interactive_config() -> Dict[str, Any]:
    """
    Interactive configuration builder.

    Returns:
        Configuration dictionary
    """
    print("\n[CONFIGURATION SETUP]")
    print("=" * 60)

    config = {}

    # Essential configuration
    print("\nESSENTIAL SETTINGS:")
    config['SHEET_ID'] = get_user_input("Google Sheet ID")
    config['TAB_NAME'] = get_user_input("Tab/Sheet Name", "Sheet1")

    # Row scope
    print("\nROW SCOPE:")
    print("  Options: 'all rows' or range like '2:100'")
    config['ROW_SCOPE'] = get_user_input("Row Scope", "all rows")

    # Link limits
    print("\nLINK LIMITS:")
    config['DAILY_LINK_LIMIT'] = get_user_input("Daily Link Limit", 500, int)
    config['MAX_LINKS_PER_ROW'] = get_user_input("Max Links Per Row", 10, int)

    # Search configuration
    print("\nSEARCH CONFIGURATION:")
    print("  Options: Google, Bing, API")
    config['SEARCH_ENGINE'] = get_user_input("Search Engine", "Google")

    # Scraping configuration
    print("\nSCRAPING CONFIGURATION:")
    print("  Options: 'light' (meta + hero) or 'deep' (key pages)")
    config['SCRAPE_DEPTH'] = get_user_input("Scrape Depth", "light")

    # ARP mode
    print("\nAUTOMATED RESEARCH & PRODUCT (ARP):")
    config['ARP_MODE'] = 'on' if get_user_input("Enable ARP Mode?", True, bool) else 'off'

    # Advanced settings
    print("\nADVANCED SETTINGS:")
    show_advanced = get_user_input("Configure advanced settings?", False, bool)

    if show_advanced:
        config['USER_AGENT_ID'] = get_user_input("User Agent ID", "LinkIntelBot/1.0")
        config['ROBOTS_RESPECT'] = get_user_input("Respect robots.txt?", True, bool)

        # Delay randomization
        min_delay = get_user_input("Min delay (ms)", 800, int)
        max_delay = get_user_input("Max delay (ms)", 2500, int)
        config['DELAY_RANDOMIZATION_MS'] = (min_delay, max_delay)

        # Retry policy
        retry_attempts = get_user_input("Retry attempts", 3, int)
        config['RETRY_POLICY'] = {
            'attempts': retry_attempts,
            'backoff': [2, 4, 8][:retry_attempts]
        }

        config['FORCE_REFRESH'] = get_user_input("Force refresh (ignore cache)?", False, bool)
    else:
        # Default advanced settings
        config['USER_AGENT_ID'] = "LinkIntelBot/1.0"
        config['ROBOTS_RESPECT'] = True
        config['DELAY_RANDOMIZATION_MS'] = (800, 2500)
        config['RETRY_POLICY'] = {'attempts': 3, 'backoff': [2, 4, 8]}
        config['FORCE_REFRESH'] = False

    return config


def load_config_file(filepath: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        filepath: Path to config file

    Returns:
        Configuration dictionary
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def save_config_file(config: Dict[str, Any], filepath: str):
    """
    Save configuration to JSON file.

    Args:
        config: Configuration dictionary
        filepath: Path to save file
    """
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"[OK] Configuration saved to {filepath}")


def run_orchestrator(config: Dict[str, Any]):
    """
    Run the Link Intelligence Orchestrator.

    Args:
        config: Configuration dictionary
    """
    print("\n[STARTING LINK INTELLIGENCE ORCHESTRATOR]")
    print("=" * 60)

    # Display configuration
    print("\nConfiguration Summary:")
    for key, value in config.items():
        if key != 'SHEET_ID':  # Don't display full sheet ID
            if key == 'SHEET_ID':
                display_value = value[:10] + "..." if len(value) > 10 else value
            else:
                display_value = value
            print(f"  {key}: {display_value}")

    # Confirmation
    print("\n")
    if not get_user_input("Proceed with this configuration?", True, bool):
        print("[CANCELLED] Operation cancelled")
        return

    # Create and run orchestrator
    try:
        orchestrator = LinkIntelligenceOrchestrator(config)
        stats = orchestrator.run()

        # Display results
        print("\n[COMPLETE] PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Duration: {(stats['end_time'] - stats['start_time']).total_seconds():.2f} seconds")

        # Offer to save configuration
        if get_user_input("\nSave this configuration for future use?", False, bool):
            filename = get_user_input("Configuration filename", "link_intel_config.json")
            save_config_file(config, filename)

    except KeyboardInterrupt:
        print("\n\n[WARNING] Processing interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        if get_user_input("Show full error trace?", False, bool):
            traceback.print_exc()


def main():
    """Main CLI entry point."""
    print_banner()

    parser = argparse.ArgumentParser(description='Link Intelligence Orchestrator CLI')
    parser.add_argument('--config', type=str, help='Path to configuration JSON file')
    parser.add_argument('--sheet-id', type=str, help='Google Sheet ID')
    parser.add_argument('--tab', type=str, default='Sheet1', help='Sheet tab name')
    parser.add_argument('--rows', type=str, default='all rows', help='Row scope')
    parser.add_argument('--daily-limit', type=int, default=500, help='Daily link limit')
    parser.add_argument('--max-per-row', type=int, default=10, help='Max links per row')
    parser.add_argument('--search', type=str, default='Google', help='Search engine')
    parser.add_argument('--depth', type=str, default='light', help='Scrape depth')
    parser.add_argument('--arp', type=str, default='on', help='ARP mode (on/off)')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh')

    args = parser.parse_args()

    # Load or create configuration
    if args.config:
        print(f"[LOADING] Loading configuration from {args.config}")
        config = load_config_file(args.config)
    elif args.sheet_id:
        # Build config from command line arguments
        config = {
            'SHEET_ID': args.sheet_id,
            'TAB_NAME': args.tab,
            'ROW_SCOPE': args.rows,
            'DAILY_LINK_LIMIT': args.daily_limit,
            'MAX_LINKS_PER_ROW': args.max_per_row,
            'SEARCH_ENGINE': args.search,
            'SCRAPE_DEPTH': args.depth,
            'ARP_MODE': args.arp,
            'USER_AGENT_ID': 'LinkIntelBot/1.0',
            'ROBOTS_RESPECT': True,
            'DELAY_RANDOMIZATION_MS': (800, 2500),
            'RETRY_POLICY': {'attempts': 3, 'backoff': [2, 4, 8]},
            'FORCE_REFRESH': args.force_refresh
        }
    else:
        # Interactive configuration
        config = interactive_config()

    # Run the orchestrator
    run_orchestrator(config)

    print("\nThank you for using Link Intelligence Orchestrator!")


if __name__ == "__main__":
    main()