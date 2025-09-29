#!/usr/bin/env python3
"""
LeadShark Version Information
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

# Import version constants from different modules
try:
    from non_destructive_enricher import PROCESSOR_VERSION as NDE_VERSION, SCHEMA_VERSION as NDE_SCHEMA
    from compact_enricher import PROCESSOR_VERSION as COMPACT_VERSION, SCHEMA_VERSION as COMPACT_SCHEMA
    from link_intelligence_orchestrator import ORCHESTRATOR_VERSION as LIO_VERSION, SCHEMA_VERSION as LIO_SCHEMA
except ImportError as e:
    print(f"Could not import all modules: {e}")
    NDE_VERSION = NDE_SCHEMA = COMPACT_VERSION = COMPACT_SCHEMA = LIO_VERSION = LIO_SCHEMA = "Unknown"

# Main version
LEADSHARK_VERSION = "2.0"
LEADSHARK_BUILD = "Production"

def show_version():
    """Display comprehensive version information"""
    print("=" * 60)
    print("LEADSHARK - PREDATORY LEAD ENRICHMENT SYSTEM")
    print("=" * 60)
    print()
    print(f"LeadShark Version: {LEADSHARK_VERSION}")
    print(f"Build: {LEADSHARK_BUILD}")
    print()
    print("COMPONENT VERSIONS:")
    print("-" * 30)
    print(f"Non-Destructive Enricher: {NDE_VERSION}")
    print(f"  Schema: {NDE_SCHEMA}")
    print(f"Compact Enricher: {COMPACT_VERSION}")
    print(f"  Schema: {COMPACT_SCHEMA}")
    print(f"Link Intelligence Orchestrator: {LIO_VERSION}")
    print(f"  Schema: {LIO_SCHEMA}")
    print()
    print("CAPABILITIES:")
    print("-" * 30)
    print("+ Google Sheets API Integration")
    print("+ Non-destructive lead enrichment")
    print("+ Multi-platform web scraping")
    print("+ API-based data enhancement")
    print("+ Rich CLI interface with progress tracking")
    print("+ OAuth2 authentication")
    print("+ Smart column management")
    print("+ JSON-structured data output")
    print()
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")

if __name__ == "__main__":
    show_version()