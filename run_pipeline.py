#!/usr/bin/env python3
"""
Google Sheets Intelligence Pipeline - Main Execution Script

Usage:
    python run_pipeline.py --test          # Test with first 5 rows
    python run_pipeline.py --all           # Process all rows
    python run_pipeline.py --rows 50       # Process first 50 rows
    python run_pipeline.py --start 10      # Start from row 10
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from google_sheets_processor import GoogleSheetsIntelligenceProcessor
    from enhanced_scraping_pipeline import DataEnrichment
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required files are in the current directory")
    sys.exit(1)

def load_config():
    """Load configuration from environment or defaults"""
    config = {
        'credentials_path': os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', './credentials.json'),
        'sheet_id': os.getenv('GOOGLE_SHEET_ID', ''),
        'max_rows_per_batch': int(os.getenv('MAX_ROWS_PER_BATCH', '50')),
        'start_row': int(os.getenv('START_ROW', '2')),
        'processing_delay': float(os.getenv('PROCESSING_DELAY', '2.0'))
    }
    
    return config

def validate_config(config):
    """Validate configuration settings"""
    errors = []
    
    if not config['sheet_id']:
        errors.append("GOOGLE_SHEET_ID not set")
    
    if not os.path.exists(config['credentials_path']):
        errors.append(f"Credentials file not found: {config['credentials_path']}")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║           Google Sheets Intelligence Pipeline               ║
║                                                              ║
║  Automated web scraping and API enrichment system           ║
║  for comprehensive business intelligence reports             ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_processing_summary(results):
    """Print processing results summary"""
    print("\\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    
    if results['status'] == 'completed':
        print(f"✅ Processing completed successfully")
        print(f"📊 Total rows: {results['total_rows']}")
        print(f"✅ Successful: {results['successful_rows']}")
        print(f"❌ Failed: {results['failed_rows']}")
        print(f"⏱️  Processing time: {results['processing_time']:.1f} seconds")
        print(f"📈 Average per row: {results['average_time_per_row']:.1f} seconds")
        
        if results.get('api_calls'):
            api_stats = results['api_calls']
            print(f"🔗 API calls: {api_stats['total']} (Success: {api_stats['successful']})")
        
        print(f"\\n💡 Success rate: {(results['successful_rows']/results['total_rows']*100):.1f}%")
        
    else:
        print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")

def main():
    """Main execution function"""
    print_banner()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Google Sheets Intelligence Pipeline')
    parser.add_argument('--test', action='store_true', help='Test mode - process first 5 rows')
    parser.add_argument('--all', action='store_true', help='Process all rows')
    parser.add_argument('--rows', type=int, help='Number of rows to process')
    parser.add_argument('--start', type=int, help='Starting row number (default: 2)')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--credentials', help='Path to Google credentials JSON file')
    parser.add_argument('--sheet-id', help='Google Sheets ID')
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be processed without making changes')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Override with command line arguments
    if args.credentials:
        config['credentials_path'] = args.credentials
    if args.sheet_id:
        config['sheet_id'] = args.sheet_id
    if args.start:
        config['start_row'] = args.start
    
    # Validate configuration
    if not validate_config(config):
        print("\\n❌ Configuration validation failed. Please fix the errors and try again.")
        return 1
    
    print(f"📋 Configuration:")
    print(f"   Credentials: {config['credentials_path']}")
    print(f"   Sheet ID: {config['sheet_id'][:20]}...")
    print(f"   Start Row: {config['start_row']}")
    
    # Determine processing parameters
    max_rows = None
    start_row = config['start_row']
    
    if args.test:
        max_rows = 5
        print(f"\\n🧪 Test Mode: Processing first {max_rows} rows")
    elif args.rows:
        max_rows = args.rows
        print(f"\\n📊 Processing {max_rows} rows starting from row {start_row}")
    elif args.all:
        print(f"\\n🚀 Processing ALL rows starting from row {start_row}")
    else:
        # Default to test mode
        max_rows = 5
        print(f"\\n🧪 Default Test Mode: Processing first {max_rows} rows")
        print("   Use --all to process all rows, or --rows N to specify count")
    
    if args.dry_run:
        print("\\n👀 DRY RUN MODE: No changes will be made to the Google Sheet")
    
    # Initialize processor
    print("\\n🔧 Initializing processor...")
    processor = GoogleSheetsIntelligenceProcessor(
        credentials_path=config['credentials_path'],
        sheet_id=config['sheet_id']
    )
    
    # Authenticate
    print("🔑 Authenticating with Google Sheets API...")
    if not processor.authenticate():
        print("❌ Authentication failed. Please check your credentials.")
        return 1
    
    print("✅ Authentication successful!")
    
    # Dry run - just read and preview
    if args.dry_run:
        print("\\n👀 Dry run - Reading sheet data...")
        sheet_data = processor.read_sheet_data()
        if sheet_data:
            headers = sheet_data[0]
            data_rows = sheet_data[1:]
            print(f"   Found {len(data_rows)} data rows")
            print(f"   Columns: {len(headers)}")
            
            # Preview first few rows
            preview_rows = min(5, len(data_rows))
            print(f"\\n   Preview of first {preview_rows} rows:")
            for i, row in enumerate(data_rows[:preview_rows], start=2):
                name = row[headers.index('name')] if 'name' in headers else 'Unknown'
                org = row[headers.index('organization_name')] if 'organization_name' in headers else 'Unknown'
                print(f"     Row {i}: {name} - {org}")
        
        print("\\n✅ Dry run completed. Use --all or --rows to process data.")
        return 0
    
    # Confirm processing
    if not args.test:
        confirm = input(f"\\n⚠️  About to process data. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Processing cancelled.")
            return 0
    
    # Start processing
    print(f"\\n🚀 Starting processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   Progress will be logged to 'sheets_processing.log'")
    
    start_time = time.time()
    
    try:
        # Process the sheet
        results = processor.process_sheet(start_row=start_row, max_rows=max_rows)
        
        # Print results
        processing_time = time.time() - start_time
        results['processing_time'] = processing_time
        
        print_processing_summary(results)
        
        # Save results to file
        results_file = f"processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\\n📁 Results saved to: {results_file}")
        
        return 0 if results['status'] == 'completed' else 1
        
    except KeyboardInterrupt:
        print("\\n\\n⚠️ Processing interrupted by user")
        print("   Progress has been saved to Google Sheets")
        print("   You can resume by running the script again")
        return 1
    
    except Exception as e:
        print(f"\\n❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())