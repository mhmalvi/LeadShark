import requests
import json
import time
from urllib.parse import quote
import re
from typing import List, Dict, Optional, Tuple

class DataEnrichment:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.results = {}
        self.email_pattern_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    def generate_email_variants(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """
        Generate common email pattern variants
        Returns list of possible email addresses
        """
        first_name = first_name.lower().strip()
        last_name = last_name.lower().strip()
        domain = domain.lower().strip()

        # Remove www. prefix if present
        domain = domain.replace('www.', '')

        # Remove http/https protocols if present
        domain = re.sub(r'^https?://', '', domain)

        # Extract domain only (remove paths)
        if '/' in domain:
            domain = domain.split('/')[0]

        variants = [
            f"{first_name}@{domain}",
            f"{first_name}.{last_name}@{domain}",
            f"{first_name[0]}.{last_name}@{domain}",
            f"{first_name}{last_name}@{domain}",
            f"{first_name[0]}{last_name}@{domain}",
            f"{last_name}.{first_name}@{domain}",
            f"{last_name}{first_name}@{domain}",
            f"{first_name}_{last_name}@{domain}",
            f"{first_name}-{last_name}@{domain}",
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for email in variants:
            if email not in seen:
                seen.add(email)
                unique_variants.append(email)

        return unique_variants

    def extract_emails_from_content(self, content: str) -> List[str]:
        """
        Extract email addresses from text content using regex
        Returns list of unique email addresses found
        """
        if not content:
            return []

        # Find all email patterns in content
        emails = re.findall(self.email_pattern_regex, content)

        # Filter out common non-personal emails
        filtered_emails = []
        exclude_patterns = ['noreply', 'no-reply', 'support', 'info', 'contact', 'admin', 'webmaster']

        for email in emails:
            email = email.lower()
            if not any(pattern in email for pattern in exclude_patterns):
                filtered_emails.append(email)

        # Remove duplicates while preserving order
        seen = set()
        unique_emails = []
        for email in filtered_emails:
            if email not in seen:
                seen.add(email)
                unique_emails.append(email)

        return unique_emails

    def verify_email_eva(self, email):
        """Verify email using EVA Email Verification API (No API key needed)"""
        try:
            url = f"https://api.eva.pingutil.com/email?email={email}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    'service': 'EVA',
                    'status': 'success',
                    'deliverable': data.get('status') == 'deliverable',
                    'confidence': 80 if data.get('status') == 'deliverable' else 20,
                    'data': data
                }
            else:
                return {'service': 'EVA', 'status': 'failed', 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            return {'service': 'EVA', 'status': 'error', 'error': str(e)}
    
    def find_email_hunter(self, domain: str, first_name: str, last_name: str, api_key: Optional[str] = None) -> Dict:
        """
        Find email using Hunter.io API
        Free tier: 25 searches/month
        """
        try:
            if not api_key:
                return {'service': 'Hunter.io', 'status': 'skipped', 'error': 'No API key provided'}

            url = f"https://api.hunter.io/v2/email-finder"
            params = {
                'domain': domain,
                'first_name': first_name,
                'last_name': last_name,
                'api_key': api_key
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                email_data = data.get('data', {})
                return {
                    'service': 'Hunter.io',
                    'status': 'success',
                    'email': email_data.get('email'),
                    'confidence': email_data.get('score', 0),
                    'deliverable': email_data.get('status') == 'valid',
                    'sources': email_data.get('sources', []),
                    'data': email_data
                }
            else:
                return {'service': 'Hunter.io', 'status': 'failed', 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            return {'service': 'Hunter.io', 'status': 'error', 'error': str(e)}

    def verify_email_zerobounce(self, email: str, api_key: Optional[str] = None) -> Dict:
        """
        Verify email using ZeroBounce API
        Free tier: 100 credits/month
        """
        try:
            if not api_key:
                return {'service': 'ZeroBounce', 'status': 'skipped', 'error': 'No API key provided'}

            url = f"https://api.zerobounce.net/v2/validate"
            params = {
                'api_key': api_key,
                'email': email
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', '')
                deliverable = status in ['valid', 'catch-all']

                return {
                    'service': 'ZeroBounce',
                    'status': 'success',
                    'deliverable': deliverable,
                    'confidence': 90 if deliverable else 10,
                    'sub_status': data.get('sub_status', ''),
                    'data': data
                }
            else:
                return {'service': 'ZeroBounce', 'status': 'failed', 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            return {'service': 'ZeroBounce', 'status': 'error', 'error': str(e)}

    def verify_email_multi_service(
        self,
        email: str,
        hunter_api_key: Optional[str] = None,
        zerobounce_api_key: Optional[str] = None
    ) -> Dict:
        """
        Verify email using multiple services with fallback
        Returns the best result based on confidence scores
        """
        results = []

        # Try EVA first (free, no API key needed)
        eva_result = self.verify_email_eva(email)
        if eva_result.get('status') == 'success':
            results.append(eva_result)

        # Try ZeroBounce if API key provided
        if zerobounce_api_key:
            time.sleep(0.5)  # Rate limiting
            zerobounce_result = self.verify_email_zerobounce(email, zerobounce_api_key)
            if zerobounce_result.get('status') == 'success':
                results.append(zerobounce_result)

        # Find best result (highest confidence)
        if results:
            best_result = max(results, key=lambda x: x.get('confidence', 0))
            best_result['verification_method'] = 'multi-service'
            best_result['services_checked'] = [r.get('service') for r in results]
            return best_result

        return {
            'service': 'Multi-service',
            'status': 'failed',
            'error': 'All verification services failed',
            'deliverable': False,
            'confidence': 0
        }

    def find_and_verify_emails(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        scraped_content: str = "",
        provided_email: Optional[str] = None,
        hunter_api_key: Optional[str] = None,
        zerobounce_api_key: Optional[str] = None
    ) -> Dict:
        """
        Complete email finding and verification pipeline
        Returns: {
            'email_variants': [],
            'extracted_emails': [],
            'best_email': '',
            'confidence_score': 0-100,
            'source': 'generated/scraped/provided',
            'all_results': []
        }
        """
        all_emails = []
        all_results = []

        # 1. Generate email variants
        generated_variants = self.generate_email_variants(first_name, last_name, domain)

        # 2. Extract emails from scraped content
        extracted_emails = self.extract_emails_from_content(scraped_content)

        # 3. Try Hunter.io if API key provided
        hunter_email = None
        if hunter_api_key:
            hunter_result = self.find_email_hunter(domain, first_name, last_name, hunter_api_key)
            if hunter_result.get('status') == 'success' and hunter_result.get('email'):
                hunter_email = hunter_result['email']
                all_results.append({
                    'email': hunter_email,
                    'confidence': hunter_result.get('confidence', 50),
                    'source': 'Hunter.io',
                    'deliverable': hunter_result.get('deliverable', False)
                })

        # 4. Combine all email candidates
        email_candidates = []
        if provided_email:
            email_candidates.append(provided_email)
        if hunter_email:
            email_candidates.append(hunter_email)
        email_candidates.extend(extracted_emails[:3])  # Top 3 extracted
        email_candidates.extend(generated_variants[:5])  # Top 5 variants

        # Remove duplicates
        unique_candidates = []
        seen = set()
        for email in email_candidates:
            email_lower = email.lower()
            if email_lower not in seen:
                seen.add(email_lower)
                unique_candidates.append(email)

        # 5. Verify each candidate
        for email in unique_candidates[:10]:  # Limit to 10 verifications
            verification = self.verify_email_multi_service(
                email,
                hunter_api_key,
                zerobounce_api_key
            )

            if verification.get('status') == 'success':
                all_results.append({
                    'email': email,
                    'confidence': verification.get('confidence', 0),
                    'source': 'verified',
                    'deliverable': verification.get('deliverable', False),
                    'service': verification.get('service')
                })

            time.sleep(0.3)  # Rate limiting

        # 6. Select best email
        best_result = None
        if all_results:
            # Prioritize deliverable emails with highest confidence
            deliverable_results = [r for r in all_results if r.get('deliverable')]
            if deliverable_results:
                best_result = max(deliverable_results, key=lambda x: x['confidence'])
            else:
                best_result = max(all_results, key=lambda x: x['confidence'])

        return {
            'email_variants': generated_variants,
            'extracted_emails': extracted_emails,
            'best_email': best_result['email'] if best_result else '',
            'confidence_score': best_result['confidence'] if best_result else 0,
            'source': best_result['source'] if best_result else 'none',
            'deliverable': best_result.get('deliverable', False) if best_result else False,
            'all_results': all_results
        }

    def verify_email_whoisxml(self, email, api_key=None):
        """Verify email using WhoisXML API (requires free API key)"""
        try:
            if not api_key:
                return {'service': 'WhoisXML', 'status': 'skipped', 'error': 'No API key provided'}

            url = f"https://emailverification.whoisxmlapi.com/api/v2?apiKey={api_key}&emailAddress={email}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    'service': 'WhoisXML',
                    'status': 'success',
                    'data': data
                }
            else:
                return {'service': 'WhoisXML', 'status': 'failed', 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            return {'service': 'WhoisXML', 'status': 'error', 'error': str(e)}
    
    def get_gender(self, first_name):
        """Get gender prediction using Gender API (500 free/month)"""
        try:
            url = f"https://api.genderize.io/?name={first_name}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'service': 'Genderize',
                    'status': 'success',
                    'gender': data.get('gender'),
                    'probability': data.get('probability'),
                    'count': data.get('count')
                }
            else:
                return {'service': 'Genderize', 'status': 'failed', 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'service': 'Genderize', 'status': 'error', 'error': str(e)}
    
    def search_github(self, company_name):
        """Search GitHub for company repositories (60 requests/hour free)"""
        try:
            # Search for organization
            search_query = quote(f'"{company_name}" OR "{company_name.replace("-", " ")}" in:name,description')
            url = f"https://api.github.com/search/users?q={search_query}&type=org"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                orgs = data.get('items', [])
                
                # Also search for repositories
                repo_url = f"https://api.github.com/search/repositories?q={search_query}"
                repo_response = self.session.get(repo_url, timeout=10)
                
                repo_data = repo_response.json() if repo_response.status_code == 200 else {}
                repos = repo_data.get('items', [])
                
                return {
                    'service': 'GitHub',
                    'status': 'success',
                    'organizations': orgs[:5],  # Top 5 matches
                    'repositories': repos[:10],  # Top 10 matches
                    'total_orgs': len(orgs),
                    'total_repos': len(repos)
                }
            else:
                return {'service': 'GitHub', 'status': 'failed', 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'service': 'GitHub', 'status': 'error', 'error': str(e)}
    
    def google_company_search(self, company_name, location=""):
        """Search Google for company information"""
        try:
            search_query = f'"{company_name}" {location} company size employees industry'
            encoded_query = quote(search_query)
            
            # Use a simple Google search scraper approach
            url = f"https://www.google.com/search?q={encoded_query}&num=10"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Extract basic information from search results
                text = response.text
                
                # Look for employee count patterns
                employee_patterns = [
                    r'(\d+)[\s-]*(?:to|-)[\s]*(\d+)?\s*employees?',
                    r'(\d+)\+?\s*employees?',
                    r'team of (\d+)',
                    r'staff of (\d+)',
                ]
                
                employees_found = []
                for pattern in employee_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    employees_found.extend(matches)
                
                # Look for industry mentions
                industry_keywords = [
                    'marketing', 'advertising', 'digital agency', 'media', 'consulting',
                    'technology', 'software', 'services', 'solutions'
                ]
                
                industries_found = []
                for keyword in industry_keywords:
                    if keyword.lower() in text.lower():
                        industries_found.append(keyword)
                
                return {
                    'service': 'Google Search',
                    'status': 'success',
                    'employee_mentions': employees_found[:5],
                    'industry_mentions': list(set(industries_found)),
                    'search_results_found': True
                }
            else:
                return {'service': 'Google Search', 'status': 'failed', 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'service': 'Google Search', 'status': 'error', 'error': str(e)}
    
    def check_linkedin_profile_exists(self, profile_url):
        """Check if LinkedIn profile exists publicly"""
        try:
            response = self.session.get(profile_url, timeout=10)
            
            exists = response.status_code not in [404, 999]  # 999 is LinkedIn's blocked response
            
            return {
                'service': 'LinkedIn Check',
                'status': 'success',
                'profile_exists': exists,
                'response_code': response.status_code,
                'accessible': response.status_code == 200
            }
                
        except Exception as e:
            return {'service': 'LinkedIn Check', 'status': 'error', 'error': str(e)}
    
    def enrich_company_data(self, company_info):
        """Main function to enrich company data using all APIs"""
        
        print("Starting data enrichment process...")
        enrichment_results = {}
        
        # Extract company details from scraped data
        company_name = "Scierka-Lang Media Solutions"
        owner_name = "Rich Scierka"
        owner_email = "rich@scierkalang.com"
        company_location = "Old Saybrook, Connecticut"
        linkedin_profile = "https://www.linkedin.com/in/scierka"
        
        # 1. Email Verification
        print("\\n1. Verifying email address...")
        enrichment_results['email_verification'] = {
            'eva': self.verify_email_eva(owner_email),
            # 'whoisxml': self.verify_email_whoisxml(owner_email)  # Requires API key
        }
        time.sleep(1)
        
        # 2. Gender Detection
        print("2. Detecting gender for owner name...")
        first_name = owner_name.split()[0]  # "Rich"
        enrichment_results['gender_detection'] = self.get_gender(first_name)
        time.sleep(1)
        
        # 3. GitHub Search
        print("3. Searching GitHub for company presence...")
        enrichment_results['github_search'] = self.search_github(company_name)
        time.sleep(2)
        
        # 4. Google Company Search
        print("4. Searching Google for additional company information...")
        enrichment_results['google_search'] = self.google_company_search(company_name, company_location)
        time.sleep(3)
        
        # 5. LinkedIn Profile Check
        print("5. Checking LinkedIn profile accessibility...")
        enrichment_results['linkedin_check'] = self.check_linkedin_profile_exists(linkedin_profile)
        
        return enrichment_results

# Helper functions for backward compatibility
def enrich_gender(name):
    """Helper function for gender enrichment - backward compatible"""
    enricher = DataEnrichment()
    first_name = name.split()[0] if ' ' in name else name
    return enricher.get_gender(first_name)

def enrich_email_verification(email):
    """Helper function for email verification - backward compatible"""
    enricher = DataEnrichment()
    return enricher.verify_email_eva(email)

def enrich_github_search(company_name):
    """Helper function for GitHub search - backward compatible"""
    enricher = DataEnrichment()
    return enricher.search_github(company_name)

# Main execution
if __name__ == "__main__":
    enricher = DataEnrichment()
    
    # Load existing scraped data
    try:
        with open('scraped_content_final.json', 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
    except FileNotFoundError:
        scraped_data = {}
        print("No existing scraped data found, proceeding with enrichment...")
    
    # Perform enrichment
    enrichment_results = enricher.enrich_company_data(scraped_data)
    
    # Save enriched results
    with open('enriched_data.json', 'w', encoding='utf-8') as f:
        json.dump(enrichment_results, f, indent=2, ensure_ascii=False)
    
    print(f"\\n{'='*60}")
    print("DATA ENRICHMENT COMPLETE")
    print(f"{'='*60}")
    
    # Print summary
    for category, data in enrichment_results.items():
        print(f"\\n{category.upper().replace('_', ' ')}:")
        
        if isinstance(data, dict):
            if 'eva' in data:  # Email verification section
                for service, result in data.items():
                    if result['status'] == 'success':
                        print(f"  {service}: Email deliverable = {result.get('deliverable', 'Unknown')}")
                    else:
                        print(f"  {service}: {result['status']} - {result.get('error', 'N/A')}")
            else:
                if data['status'] == 'success':
                    if category == 'gender_detection':
                        print(f"  Gender: {data.get('gender', 'Unknown')} (Probability: {data.get('probability', 'N/A')})")
                    elif category == 'github_search':
                        print(f"  Found {data.get('total_orgs', 0)} organizations, {data.get('total_repos', 0)} repositories")
                    elif category == 'google_search':
                        print(f"  Employee mentions: {data.get('employee_mentions', [])}")
                        print(f"  Industries: {data.get('industry_mentions', [])}")
                    elif category == 'linkedin_check':
                        print(f"  Profile exists: {data.get('profile_exists', False)}")
                        print(f"  Accessible: {data.get('accessible', False)}")
                else:
                    print(f"  Status: {data['status']} - {data.get('error', 'N/A')}")
    
    print(f"\\nResults saved to 'enriched_data.json'")
    print("Ready to generate enhanced report!")