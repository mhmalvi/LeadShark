#!/usr/bin/env python3
"""
Lead Scoring Engine with Weighted Factors
Generates lead scores (0-100) and classifications (Hot/Warm/Cold/Discard)
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class LeadScoringEngine:
    """
    Lead scoring with weighted factors:
    - Role / Decision Power: 30%
    - Company Fit: 25%
    - Engagement / Visibility: 15%
    - Contactability: 15%
    - Tech / Product Fit: 10%
    - Recency / Signal Strength: 5%
    """

    def __init__(self):
        self.weights = {
            'role': 30,
            'company_fit': 25,
            'engagement': 15,
            'contactability': 15,
            'tech_fit': 10,
            'recency': 5
        }

        # Decision-making titles
        self.executive_titles = [
            'ceo', 'chief executive', 'founder', 'co-founder', 'president',
            'cto', 'chief technology', 'cio', 'chief information',
            'cfo', 'chief financial', 'cmo', 'chief marketing',
            'vp', 'vice president', 'head of', 'director', 'managing director'
        ]

        # Technical indicators
        self.technical_keywords = [
            'engineer', 'developer', 'architect', 'devops', 'sre',
            'data scientist', 'machine learning', 'ai', 'cloud',
            'api', 'software', 'platform', 'infrastructure'
        ]

    def calculate_score(self, enrichment_data: Dict) -> Tuple[int, str, Dict[str, float]]:
        """
        Calculate lead score and classification
        Returns: (score, tag, breakdown)
        """
        scores = {
            'role': self._score_role(enrichment_data),
            'company_fit': self._score_company_fit(enrichment_data),
            'engagement': self._score_engagement(enrichment_data),
            'contactability': self._score_contactability(enrichment_data),
            'tech_fit': self._score_tech_fit(enrichment_data),
            'recency': self._score_recency(enrichment_data)
        }

        # Calculate weighted total
        total_score = 0
        for factor, weight in self.weights.items():
            total_score += scores[factor] * weight

        # Round to integer
        total_score = int(round(total_score))

        # Determine tag
        tag = self._get_lead_tag(total_score)

        # Return score, tag, and breakdown
        breakdown = {f"{k}_score": round(v * 100, 1) for k, v in scores.items()}

        return total_score, tag, breakdown

    def _score_role(self, data: Dict) -> float:
        """Score based on role/decision power (0.0-1.0)"""
        score = 0.0

        # Check title/headline from LinkedIn
        title = self._get_nested_value(data, ['scraped_content', 'linkedin', 'extracted', 'title'], '')
        headline = self._get_nested_value(data, ['scraped_content', 'linkedin', 'extracted', 'key_fields', 'headline'], '')

        combined_title = f"{title} {headline}".lower()

        # Executive/Founder level = 1.0
        if any(exec_title in combined_title for exec_title in ['ceo', 'founder', 'co-founder', 'chief executive', 'president']):
            score = 1.0
        # C-level = 0.9
        elif any(c_level in combined_title for c_level in ['cto', 'cfo', 'cmo', 'cio', 'chief']):
            score = 0.9
        # VP/Director = 0.7
        elif any(title_word in combined_title for title_word in ['vp', 'vice president', 'director', 'head of']):
            score = 0.7
        # Manager = 0.5
        elif any(title_word in combined_title for title_word in ['manager', 'lead', 'senior']):
            score = 0.5
        # Other roles = 0.3
        elif combined_title.strip():
            score = 0.3

        return score

    def _score_company_fit(self, data: Dict) -> float:
        """Score based on company fit (0.0-1.0)"""
        score = 0.5  # Default moderate fit

        # Company size indicators
        company_info = self._get_nested_value(data, ['api_results', 'google_search', 'company_info'], '')
        company_industry = self._get_nested_value(data, ['api_results', 'google_search', 'industry_mentions'], [])

        # Target industries (adjust based on your ICP)
        target_industries = ['saas', 'software', 'technology', 'cloud', 'ai', 'digital']

        if company_industry:
            matching_industries = [ind for ind in company_industry if any(target in ind.lower() for target in target_industries)]
            if len(matching_industries) >= 2:
                score = 0.8
            elif len(matching_industries) == 1:
                score = 0.6

        # Boost for funded companies
        if any(keyword in str(company_info).lower() for keyword in ['series', 'funding', 'raised', 'venture']):
            score = min(1.0, score + 0.2)

        return score

    def _score_engagement(self, data: Dict) -> float:
        """Score based on engagement/visibility (0.0-1.0)"""
        score = 0.0

        # Twitter/X followers
        twitter_followers = self._get_nested_value(data, ['scraped_content', 'twitter', 'extracted', 'metrics', 'followers'], 0)
        if twitter_followers:
            if twitter_followers > 10000:
                score = max(score, 1.0)
            elif twitter_followers > 5000:
                score = max(score, 0.8)
            elif twitter_followers > 1000:
                score = max(score, 0.6)
            else:
                score = max(score, 0.4)

        # LinkedIn connections (if available)
        linkedin_connections = self._get_nested_value(data, ['scraped_content', 'linkedin', 'extracted', 'key_fields', 'connections'], 0)
        if linkedin_connections:
            if linkedin_connections > 5000:
                score = max(score, 0.9)
            elif linkedin_connections > 1000:
                score = max(score, 0.7)
            elif linkedin_connections > 500:
                score = max(score, 0.5)

        # GitHub activity
        github_repos = self._get_nested_value(data, ['api_results', 'github', 'total_repos'], 0)
        if github_repos > 20:
            score = max(score, 0.7)
        elif github_repos > 10:
            score = max(score, 0.5)
        elif github_repos > 0:
            score = max(score, 0.3)

        return score

    def _score_contactability(self, data: Dict) -> float:
        """Score based on contact availability (0.0-1.0)"""
        score = 0.0

        # Email available and verified
        email_status = self._get_nested_value(data, ['api_results', 'email_verification', 'deliverable'], False)
        if email_status:
            score += 0.6

        # Phone available
        phones = self._get_nested_value(data, ['scraped_content', 'website', 'extracted', 'contacts', 'phones'], [])
        if phones:
            score += 0.2

        # Public email on website
        emails = self._get_nested_value(data, ['scraped_content', 'website', 'extracted', 'contacts', 'emails'], [])
        if emails:
            score = min(1.0, score + 0.2)

        return min(1.0, score)

    def _score_tech_fit(self, data: Dict) -> float:
        """Score based on tech/product fit (0.0-1.0)"""
        score = 0.0

        # Check for technical background
        title = self._get_nested_value(data, ['scraped_content', 'linkedin', 'extracted', 'title'], '').lower()
        bio = self._get_nested_value(data, ['scraped_content', 'linkedin', 'extracted', 'description'], '').lower()

        combined_text = f"{title} {bio}"

        # Count technical keywords
        tech_matches = sum(1 for keyword in self.technical_keywords if keyword in combined_text)

        if tech_matches >= 3:
            score = 0.9
        elif tech_matches >= 2:
            score = 0.7
        elif tech_matches >= 1:
            score = 0.5
        else:
            score = 0.2

        # Check GitHub presence
        github_repos = self._get_nested_value(data, ['api_results', 'github', 'total_repos'], 0)
        if github_repos > 0:
            score = min(1.0, score + 0.3)

        return min(1.0, score)

    def _score_recency(self, data: Dict) -> float:
        """Score based on recency/signal strength (0.0-1.0)"""
        score = 0.5  # Default

        # Check for recent activity indicators
        # Recent tweets (if available)
        recent_tweets = self._get_nested_value(data, ['scraped_content', 'twitter', 'extracted', 'key_fields', 'recent_tweets'], [])
        if recent_tweets:
            score = 0.8

        # Recent news/press mentions
        company_info = self._get_nested_value(data, ['api_results', 'google_search', 'company_info'], '').lower()
        if any(keyword in company_info for keyword in ['recently', 'just', 'announced', 'launches', 'new']):
            score = 1.0

        # Job posting indicator (hiring = growth signal)
        if 'job' in str(data).lower() or 'hiring' in str(data).lower():
            score = max(score, 0.7)

        return score

    def _get_lead_tag(self, score: int) -> str:
        """Convert score to lead tag"""
        if score >= 80:
            return "Hot 🔥"
        elif score >= 60:
            return "Warm 🟡"
        elif score >= 30:
            return "Cold 🔵"
        else:
            return "Discard ⚫"

    def _get_nested_value(self, data: Dict, keys: List[str], default=None):
        """Safely get nested dictionary value"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current if current is not None else default

    def generate_score_explanation(self, breakdown: Dict[str, float], total_score: int) -> str:
        """Generate human-readable score explanation"""
        lines = [
            f"Total Score: {total_score}/100",
            "",
            "Breakdown:"
        ]

        factor_names = {
            'role_score': 'Role / Decision Power (30%)',
            'company_fit_score': 'Company Fit (25%)',
            'engagement_score': 'Engagement / Visibility (15%)',
            'contactability_score': 'Contactability (15%)',
            'tech_fit_score': 'Tech / Product Fit (10%)',
            'recency_score': 'Recency / Signal (5%)'
        }

        for key, name in factor_names.items():
            score = breakdown.get(key, 0)
            bar = '█' * int(score / 10) + '░' * (10 - int(score / 10))
            lines.append(f"  {name}: {bar} {score:.1f}%")

        return "\n".join(lines)


# Test function
if __name__ == "__main__":
    scorer = LeadScoringEngine()

    # Test data
    test_data = {
        'scraped_content': {
            'linkedin': {
                'extracted': {
                    'title': 'CEO',
                    'key_fields': {
                        'headline': 'Founder & CEO at StartupX',
                        'connections': 1200
                    }
                }
            },
            'website': {
                'extracted': {
                    'contacts': {
                        'emails': ['john@startupx.com'],
                        'phones': ['+1-555-0100']
                    }
                }
            },
            'twitter': {
                'extracted': {
                    'metrics': {
                        'followers': 12000
                    }
                }
            }
        },
        'api_results': {
            'email_verification': {
                'deliverable': True
            },
            'github': {
                'total_repos': 45
            },
            'google_search': {
                'company_info': 'Recently raised Series A funding',
                'industry_mentions': ['saas', 'software', 'cloud']
            }
        }
    }

    score, tag, breakdown = scorer.calculate_score(test_data)
    explanation = scorer.generate_score_explanation(breakdown, score)

    print("Lead Scoring Test\n")
    print(f"Score: {score}/100")
    print(f"Tag: {tag}")
    print(f"\n{explanation}")