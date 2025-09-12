import os
import json
import time
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Google API packages not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# Import our enhanced scraping and API modules
from data_enrichment import DataEnrichment

class GoogleSheetsIntelligenceProcessor:
    """
    Automated Google Sheets intelligence processing system
    Processes rows, scrapes URLs, enriches with APIs, generates reports
    """
    
    def __init__(self, credentials_path: str, sheet_id: str):
        """
        Initialize the processor
        
        Args:
            credentials_path: Path to Google service account credentials JSON
            sheet_id: Google Sheets ID from the URL
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.service = None
        self.data_enricher = DataEnrichment()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('sheets_processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Processing statistics
        self.stats = {
            'total_rows': 0,
            'processed_rows': 0,
            'successful_rows': 0,
            'failed_rows': 0,
            'start_time': None,
            'api_calls': {'total': 0, 'successful': 0, 'failed': 0}
        }
    
    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API"""
        try:
            if not os.path.exists(self.credentials_path):
                self.logger.error(f"Credentials file not found: {self.credentials_path}")
                return False
            
            # Define the scopes
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            
            # Load credentials
            creds = Credentials.from_service_account_file(
                self.credentials_path, scopes=SCOPES
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=creds)
            self.logger.info("Successfully authenticated with Google Sheets API")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def read_sheet_data(self, range_name: str = "Sheet1!A:ZZ") -> Optional[List[List[Any]]]:
        """Read data from Google Sheets"""
        try:
            if not self.service:
                self.logger.error("Not authenticated. Call authenticate() first.")
                return None
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            self.logger.info(f"Read {len(values)} rows from Google Sheets")
            return values
            
        except HttpError as error:
            self.logger.error(f"Failed to read sheet data: {error}")
            return None
    
    def write_to_sheet(self, range_name: str, values: List[List[Any]]) -> bool:
        """Write data to Google Sheets"""
        try:
            if not self.service:
                self.logger.error("Not authenticated. Call authenticate() first.")
                return False
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self.logger.info(f"Updated {result.get('updatedCells')} cells")
            return True
            
        except HttpError as error:
            self.logger.error(f"Failed to write to sheet: {error}")
            return False
    
    def extract_urls_from_row(self, row_data: Dict) -> Dict[str, str]:
        """Extract URLs from a row of data"""
        urls = {}
        
        # Map of URL types to column keys (adjust based on your actual column names)
        url_mappings = {
            'linkedin_url': ['linkedin_url'],
            'organization_website_url': ['organization_website_url'],
            'organization_linkedin_url': ['organization_linkedin_url'],
            'organization_twitter_url': ['organization_twitter_url'],
            'organization_facebook_url': ['organization_facebook_url']
        }
        
        for url_type, possible_keys in url_mappings.items():
            for key in possible_keys:
                if key in row_data and row_data[key] and row_data[key].strip():
                    url = row_data[key].strip()
                    if url.startswith(('http://', 'https://')):
                        urls[url_type] = url
                        break
        
        return urls
    
    def scrape_urls_for_person(self, person_data: Dict, urls: Dict[str, str]) -> Dict:
        """Scrape all URLs for a person and enrich with API data"""
        self.logger.info(f"Processing URLs for {person_data.get('name', 'Unknown')}")
        
        scraping_results = {}
        api_results = {}
        
        # Scrape each URL
        for url_type, url in urls.items():
            try:
                self.logger.info(f"Scraping {url_type}: {url}")
                
                # Use enhanced scraping from our data_enrichment module
                result = self.data_enricher.scrape_url_enhanced(url)
                scraping_results[url_type] = result
                
                # Add delay to be respectful
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {str(e)}")
                scraping_results[url_type] = {
                    'status': 'failed',
                    'error': str(e),
                    'url': url
                }
        
        # API Enrichment
        try:
            # Extract first name for gender detection
            first_name = person_data.get('first_name', '').strip()
            if first_name:
                api_results['gender'] = self.data_enricher.get_gender(first_name)
            
            # Email verification (if email exists)
            email = person_data.get('email', '').strip()
            if email:
                api_results['email_verification'] = self.data_enricher.verify_email_eva(email)
            
            # GitHub search for organization
            org_name = person_data.get('organization_name', '').strip()
            if org_name:
                api_results['github_search'] = self.data_enricher.search_github(org_name)
            
            # Google search for company information
            if org_name:
                location = person_data.get('organization_city', '') + ' ' + person_data.get('organization_state', '')
                api_results['google_search'] = self.data_enricher.google_company_search(org_name, location.strip())
            
            self.stats['api_calls']['total'] += 4
            self.stats['api_calls']['successful'] += len([r for r in api_results.values() if r.get('status') == 'success'])
            
        except Exception as e:
            self.logger.error(f"API enrichment failed: {str(e)}")
            api_results['error'] = str(e)
        
        return {
            'scraping_results': scraping_results,
            'api_results': api_results,
            'person_data': person_data,
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def generate_intelligence_report(self, processing_results: Dict) -> str:
        """Generate comprehensive markdown intelligence report"""
        
        person_data = processing_results['person_data']
        scraping_results = processing_results['scraping_results']
        api_results = processing_results['api_results']
        
        # Generate report
        report = f"""# Intelligence Report: {person_data.get('name', 'Unknown')}

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Organization:** {person_data.get('organization_name', 'Unknown')}  
**Title:** {person_data.get('title', 'Unknown')}  

---

## 👤 Person Profile

**Basic Information:**
- **Name:** {person_data.get('name', 'N/A')}
- **Title:** {person_data.get('title', 'N/A')}
- **Email:** {person_data.get('email', 'N/A')}
- **LinkedIn:** {person_data.get('linkedin_url', 'N/A')}

"""
        
        # Add gender analysis if available
        if 'gender' in api_results and api_results['gender'].get('status') == 'success':
            gender_data = api_results['gender']
            report += f"""**Demographics:**
- **Gender:** {gender_data.get('gender', 'Unknown')} ({gender_data.get('probability', 0)*100:.0f}% confidence)
- **Data Source:** {gender_data.get('count', 0):,} name samples

"""
        
        # Add organization information
        report += f"""## 🏢 Organization Analysis

**Company Details:**
- **Name:** {person_data.get('organization_name', 'N/A')}
- **Website:** {person_data.get('organization_website_url', 'N/A')}
- **Industry:** {person_data.get('industry', 'N/A')}
- **Employees:** {person_data.get('estimated_num_employees', 'N/A')}
- **Founded:** {person_data.get('organization_founded_year', 'N/A')}

"""
        
        # Add scraping results summary
        report += "## 🔍 Web Presence Analysis\\n\\n"
        
        successful_scrapes = 0
        total_scrapes = len(scraping_results)
        
        for url_type, result in scraping_results.items():
            status = "✅" if result.get('status') == 'success' else "❌"
            if result.get('status') == 'success':
                successful_scrapes += 1
            report += f"- **{url_type.replace('_', ' ').title()}:** {status} {result.get('url', '')[:50]}...\\n"
        
        report += f"\\n**Summary:** {successful_scrapes}/{total_scrapes} URLs successfully processed\\n\\n"
        
        # Add API enrichment results
        if api_results:
            report += "## 🔬 API Enrichment Results\\n\\n"
            
            # Email verification
            if 'email_verification' in api_results:
                email_result = api_results['email_verification']
                if email_result.get('status') == 'success':
                    deliverable = "✅ Deliverable" if email_result.get('deliverable') else "❌ Not Deliverable"
                    report += f"**Email Verification:** {deliverable}\\n"
                else:
                    report += f"**Email Verification:** ⚠️ {email_result.get('error', 'Failed')}\\n"
            
            # GitHub presence
            if 'github_search' in api_results:
                github_result = api_results['github_search']
                if github_result.get('status') == 'success':
                    orgs = github_result.get('total_orgs', 0)
                    repos = github_result.get('total_repos', 0)
                    report += f"**GitHub Presence:** {orgs} organizations, {repos} repositories\\n"
            
            # Google search insights
            if 'google_search' in api_results:
                google_result = api_results['google_search']
                if google_result.get('status') == 'success':
                    industries = google_result.get('industry_mentions', [])
                    report += f"**Industry Keywords:** {', '.join(industries[:5])}\\n"
            
            report += "\\n"
        
        # Add recommendations
        report += """## 🎯 Engagement Recommendations

**Immediate Actions:**
1. Review LinkedIn profile for professional background
2. Analyze company website for service offerings
3. Check social media presence for engagement opportunities

**Research Priorities:**
1. Verify contact information accuracy
2. Understand company's current marketing challenges
3. Identify decision-making process and timeline

---

*This report was automatically generated using web scraping and API enrichment technologies.*
"""
        
        return report
    
    def process_single_row(self, row_index: int, row_data: Dict) -> Dict:
        """Process a single row of data"""
        self.logger.info(f"Processing row {row_index}: {row_data.get('name', 'Unknown')}")
        
        try:
            # Extract URLs
            urls = self.extract_urls_from_row(row_data)
            
            if not urls:
                self.logger.warning(f"No valid URLs found in row {row_index}")
                return {
                    'status': 'skipped',
                    'reason': 'No valid URLs found',
                    'report': '# No URLs Available\\n\\nNo valid URLs were found for processing in this record.'
                }
            
            # Scrape and enrich
            processing_results = self.scrape_urls_for_person(row_data, urls)
            
            # Generate report
            report = self.generate_intelligence_report(processing_results)
            
            self.stats['successful_rows'] += 1
            
            return {
                'status': 'success',
                'report': report,
                'processing_results': processing_results
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process row {row_index}: {str(e)}")
            self.stats['failed_rows'] += 1
            
            return {
                'status': 'failed',
                'error': str(e),
                'report': f'# Processing Failed\\n\\nError: {str(e)}'
            }
    
    def process_sheet(self, start_row: int = 2, max_rows: Optional[int] = None) -> Dict:
        """Process the entire sheet row by row"""
        
        self.stats['start_time'] = time.time()
        
        try:
            # Read sheet data
            sheet_data = self.read_sheet_data()
            if not sheet_data:
                return {'status': 'failed', 'error': 'Could not read sheet data'}
            
            # Convert to DataFrame for easier handling
            if len(sheet_data) < 2:
                return {'status': 'failed', 'error': 'Sheet appears to be empty or has no data rows'}
            
            headers = sheet_data[0]
            data_rows = sheet_data[1:]
            
            # Limit rows if specified
            if max_rows:
                data_rows = data_rows[:max_rows]
            
            self.stats['total_rows'] = len(data_rows)
            self.logger.info(f"Processing {self.stats['total_rows']} rows")
            
            # Process each row
            results = []
            
            for i, row in enumerate(data_rows[start_row-2:], start=start_row):
                # Convert row to dictionary
                row_dict = {}
                for j, header in enumerate(headers):
                    if j < len(row):
                        row_dict[header] = row[j]
                    else:
                        row_dict[header] = ''
                
                # Process row
                result = self.process_single_row(i, row_dict)
                results.append(result)
                
                # Update sheet with report (find the right column for reports)
                report_column = len(headers) + 1  # Add to next available column
                report_range = f"Sheet1!{chr(64 + report_column)}{i}:{chr(64 + report_column)}{i}"
                
                self.write_to_sheet(report_range, [[result['report']]])
                
                self.stats['processed_rows'] += 1
                
                # Add delay between rows to be respectful
                time.sleep(1)
                
                # Log progress
                if (i - start_row + 1) % 10 == 0:
                    self.logger.info(f"Progress: {i - start_row + 1}/{len(data_rows)} rows processed")
            
            # Calculate final statistics
            end_time = time.time()
            processing_time = end_time - self.stats['start_time']
            
            summary = {
                'status': 'completed',
                'total_rows': self.stats['total_rows'],
                'processed_rows': self.stats['processed_rows'],
                'successful_rows': self.stats['successful_rows'],
                'failed_rows': self.stats['failed_rows'],
                'processing_time': processing_time,
                'average_time_per_row': processing_time / self.stats['processed_rows'] if self.stats['processed_rows'] > 0 else 0,
                'api_calls': self.stats['api_calls']
            }
            
            self.logger.info(f"Processing completed: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Sheet processing failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

# Usage example and main function
if __name__ == "__main__":
    # Configuration
    CREDENTIALS_PATH = "path/to/your/credentials.json"  # Update this path
    SHEET_ID = "your_google_sheet_id_here"  # Update this ID
    
    # Initialize processor
    processor = GoogleSheetsIntelligenceProcessor(CREDENTIALS_PATH, SHEET_ID)
    
    # Authenticate
    if not processor.authenticate():
        print("Failed to authenticate. Please check your credentials.")
        exit(1)
    
    # Process sheet (start from row 2, process first 5 rows as test)
    print("Starting sheet processing...")
    results = processor.process_sheet(start_row=2, max_rows=5)
    
    print("\\nProcessing Results:")
    print(json.dumps(results, indent=2))