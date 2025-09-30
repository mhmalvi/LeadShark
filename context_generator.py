#!/usr/bin/env python3
"""
Complete Context Generator
Synthesizes all link data + API enrichments into professional paragraph format
"""

from typing import Dict, List, Optional


class ContextGenerator:
    """Generate comprehensive context paragraphs from enrichment data"""

    def __init__(self):
        pass

    def generate_complete_context(self, enrichment_data: Dict, person_name: str = "") -> str:
        """
        Generate a 3-6 sentence professional context paragraph
        combining all scraped and API data
        """
        sentences = []

        # 1. Introduction sentence (name + role + company)
        intro = self._generate_intro_sentence(enrichment_data, person_name)
        if intro:
            sentences.append(intro)

        # 2. Company/business sentence
        company_info = self._generate_company_sentence(enrichment_data)
        if company_info:
            sentences.append(company_info)

        # 3. Social/engagement sentence
        social_info = self._generate_social_sentence(enrichment_data)
        if social_info:
            sentences.append(social_info)

        # 4. Contact/verification sentence
        contact_info = self._generate_contact_sentence(enrichment_data)
        if contact_info:
            sentences.append(contact_info)

        # 5. Technical/GitHub sentence (if relevant)
        tech_info = self._generate_tech_sentence(enrichment_data)
        if tech_info:
            sentences.append(tech_info)

        # 6. Signal/opportunity sentence
        signal_info = self._generate_signal_sentence(enrichment_data)
        if signal_info:
            sentences.append(signal_info)

        # Combine sentences
        if sentences:
            return " ".join(sentences)
        else:
            return "Insufficient data to generate context."

    def _generate_intro_sentence(self, data: Dict, person_name: str) -> str:
        """Generate introduction sentence"""
        # Get name
        name = person_name or self._get_nested(data, ['scraped_content', 'linkedin', 'extracted', 'name'], '')

        # Get title
        title = self._get_nested(data, ['scraped_content', 'linkedin', 'extracted', 'title'], '')
        headline = self._get_nested(data, ['scraped_content', 'linkedin', 'extracted', 'key_fields', 'headline'], '')

        # Get company
        company = self._get_nested(data, ['scraped_content', 'linkedin', 'extracted', 'company'], '')
        if not company:
            company = self._get_nested(data, ['scraped_content', 'website', 'extracted', 'company'], '')

        # Get location
        location = self._get_nested(data, ['scraped_content', 'linkedin', 'extracted', 'location'], '')

        # Build sentence
        parts = []
        if name:
            parts.append(name)
        else:
            parts.append("This contact")

        if title or headline:
            role = title or headline
            parts.append(f"is {role}")

        if company:
            if len(parts) > 1:
                parts.append(f"at {company}")
            else:
                parts.append(f"works at {company}")

        if location:
            parts.append(f"based in {location}")

        if len(parts) > 1:
            # Build sentence from parts
            sentence = parts[0]
            if len(parts) > 1:
                sentence += " " + " ".join(parts[1:])
            return sentence + "."

        return ""

    def _generate_company_sentence(self, data: Dict) -> str:
        """Generate company/business sentence"""
        # Get website info
        website_desc = self._get_nested(data, ['scraped_content', 'website', 'extracted', 'description'], '')
        website_url = self._get_nested(data, ['scraped_content', 'website', 'url'], '')

        # Get company info from Google
        company_info = self._get_nested(data, ['api_results', 'google_search', 'company_info'], '')
        industry_mentions = self._get_nested(data, ['api_results', 'google_search', 'industry_mentions'], [])

        # Build sentence
        parts = []

        if website_desc:
            # Clean description
            desc = website_desc[:200].strip()
            if not desc.endswith('.'):
                desc += '.'
            parts.append(desc)

        if industry_mentions:
            industries = ", ".join(industry_mentions[:3])
            parts.append(f"The company operates in {industries}.")

        if company_info and not parts:
            parts.append(company_info[:150] + ".")

        if parts:
            return " ".join(parts)

        return ""

    def _generate_social_sentence(self, data: Dict) -> str:
        """Generate social media/engagement sentence"""
        # Twitter/X
        twitter_followers = self._get_nested(data, ['scraped_content', 'twitter', 'extracted', 'metrics', 'followers'], 0)
        twitter_handle = self._get_nested(data, ['scraped_content', 'twitter', 'extracted', 'key_fields', 'handle'], '')

        # LinkedIn
        linkedin_connections = self._get_nested(data, ['scraped_content', 'linkedin', 'extracted', 'key_fields', 'connections'], 0)

        parts = []

        if twitter_followers and twitter_followers > 0:
            followers_k = twitter_followers / 1000
            if followers_k >= 1:
                parts.append(f"Active on Twitter with {followers_k:.1f}k followers")
            else:
                parts.append(f"Active on Twitter with {twitter_followers} followers")

        if linkedin_connections and linkedin_connections > 0:
            connections_k = linkedin_connections / 1000
            if connections_k >= 1:
                parts.append(f"LinkedIn network of {connections_k:.1f}k+ connections")
            else:
                parts.append(f"LinkedIn network of {linkedin_connections}+ connections")

        if parts:
            return " and ".join(parts) + "."

        return ""

    def _generate_contact_sentence(self, data: Dict) -> str:
        """Generate contact/verification sentence"""
        # Email verification
        email_deliverable = self._get_nested(data, ['api_results', 'email_verification', 'deliverable'], False)
        email_status = self._get_nested(data, ['api_results', 'email_verification', 'status'], '')

        # Gender detection
        gender = self._get_nested(data, ['api_results', 'gender', 'gender'], '')
        gender_prob = self._get_nested(data, ['api_results', 'gender', 'probability'], 0)

        # Contact info
        emails = self._get_nested(data, ['scraped_content', 'website', 'extracted', 'contacts', 'emails'], [])
        phones = self._get_nested(data, ['scraped_content', 'website', 'extracted', 'contacts', 'phones'], [])

        parts = []

        if email_deliverable:
            parts.append("Email verified and deliverable")

        if emails and not email_deliverable:
            parts.append(f"Contact email available ({emails[0]})")

        if gender and gender_prob > 0.8:
            prob_pct = int(gender_prob * 100)
            parts.append(f"identified as {gender} ({prob_pct}% confidence)")

        if phones:
            parts.append(f"phone number on file")

        if parts:
            return " ".join([parts[0].capitalize()] + parts[1:]) + "."

        return ""

    def _generate_tech_sentence(self, data: Dict) -> str:
        """Generate technical/GitHub sentence"""
        # GitHub data
        github_repos = self._get_nested(data, ['api_results', 'github', 'total_repos'], 0)
        github_orgs = self._get_nested(data, ['api_results', 'github', 'organizations'], [])

        # Check for technical title
        title = self._get_nested(data, ['scraped_content', 'linkedin', 'extracted', 'title'], '').lower()
        technical_keywords = ['engineer', 'developer', 'architect', 'cto', 'technical']
        is_technical = any(keyword in title for keyword in technical_keywords)

        parts = []

        if github_repos > 0:
            if github_repos > 20:
                parts.append(f"Highly active on GitHub with {github_repos} public repositories")
            elif github_repos > 5:
                parts.append(f"Active GitHub profile with {github_repos} repositories")
            else:
                parts.append(f"GitHub presence with {github_repos} repositories")

        if github_orgs and len(github_orgs) > 0:
            org_names = ", ".join([org.get('login', '') for org in github_orgs[:2]])
            parts.append(f"member of {org_names} organizations")

        if parts and is_technical:
            return " ".join([parts[0]] + [f"and {p}" if i > 0 else p for i, p in enumerate(parts[1:])]) + "."

        return ""

    def _generate_signal_sentence(self, data: Dict) -> str:
        """Generate signal/opportunity sentence"""
        # Check for positive signals
        company_info = self._get_nested(data, ['api_results', 'google_search', 'company_info'], '').lower()

        signals = []

        # Funding signals
        if any(keyword in company_info for keyword in ['series', 'funding', 'raised', 'million']):
            if 'series a' in company_info:
                signals.append("recently completed Series A funding")
            elif 'series b' in company_info:
                signals.append("completed Series B funding")
            elif 'raised' in company_info:
                signals.append("recent funding round")

        # Growth signals
        if any(keyword in company_info for keyword in ['hiring', 'expanding', 'growing']):
            signals.append("actively hiring and expanding")

        # News signals
        if any(keyword in company_info for keyword in ['announced', 'launches', 'unveiled']):
            signals.append("recent product announcements")

        # Lead priority
        if signals:
            return " ".join(signals).capitalize() + " — high-priority lead."
        else:
            return "Potential opportunity for outreach."

    def _get_nested(self, data: Dict, keys: List[str], default=None):
        """Safely get nested dictionary value"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current if current is not None else default

    def generate_short_summary(self, enrichment_data: Dict, max_length: int = 200) -> str:
        """Generate a short summary (under max_length characters)"""
        context = self.generate_complete_context(enrichment_data)
        if len(context) <= max_length:
            return context

        # Truncate to max_length
        truncated = context[:max_length].rsplit('.', 1)[0]
        return truncated + "."


# Test function
if __name__ == "__main__":
    generator = ContextGenerator()

    test_data = {
        'scraped_content': {
            'linkedin': {
                'extracted': {
                    'name': 'John Doe',
                    'title': 'CEO',
                    'company': 'StartupX',
                    'location': 'New York',
                    'key_fields': {
                        'headline': 'Founder & CEO at StartupX',
                        'connections': 1200
                    }
                }
            },
            'website': {
                'url': 'https://startupx.com',
                'extracted': {
                    'description': 'AI-based cloud integration platform for enterprises',
                    'company': 'StartupX',
                    'contacts': {
                        'emails': ['john@startupx.com'],
                        'phones': ['+1-555-0100']
                    }
                }
            },
            'twitter': {
                'extracted': {
                    'key_fields': {
                        'handle': '@johndoe'
                    },
                    'metrics': {
                        'followers': 12000
                    }
                }
            }
        },
        'api_results': {
            'email_verification': {
                'deliverable': True,
                'status': 'success'
            },
            'gender': {
                'gender': 'male',
                'probability': 0.99
            },
            'github': {
                'total_repos': 45,
                'organizations': []
            },
            'google_search': {
                'company_info': 'StartupX recently raised Series A funding of $5M',
                'industry_mentions': ['SaaS', 'Cloud Computing', 'AI']
            }
        }
    }

    print("Complete Context Generator Test\n")
    print("=" * 60)
    context = generator.generate_complete_context(test_data, "John Doe")
    print(context)
    print("=" * 60)
    print(f"\nLength: {len(context)} characters")
    print(f"Sentences: {context.count('.')}")