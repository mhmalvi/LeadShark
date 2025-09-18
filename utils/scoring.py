"""
Deterministic lead scoring system with weighted rubric.

Provides consistent, reproducible lead scoring based on multiple
factors including relevance, purchase intent, authority, recency, and data quality.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

from .logging import get_logger

logger = get_logger(__name__)


class LeadScorer:
    """Deterministic lead scoring with weighted rubric."""

    def __init__(self):
        """Initialize lead scorer with weighted rubric."""
        # Scoring weights (must sum to 100)
        self.weights = {
            'relevance': 30,      # Relevance to our services
            'purchase_intent': 25, # Purchase intent signals
            'authority': 20,      # Authority/size indicators
            'recency': 15,        # Recent activity
            'data_quality': 10    # Data quality/consistency
        }

        # Scoring keywords and patterns
        self.scoring_patterns = {
            'relevance': {
                'high': [
                    'saas', 'software', 'technology', 'digital', 'automation',
                    'platform', 'api', 'integration', 'cloud', 'data',
                    'analytics', 'marketing', 'sales', 'crm', 'lead generation'
                ],
                'medium': [
                    'business', 'service', 'solution', 'consulting',
                    'agency', 'startup', 'company', 'organization'
                ],
                'low': []
            },
            'purchase_intent': {
                'high': [
                    'pricing', 'plans', 'contact sales', 'get started',
                    'free trial', 'demo', 'quote', 'buy now', 'purchase',
                    'subscription', 'upgrade', 'enterprise'
                ],
                'medium': [
                    'solution', 'service', 'product', 'offering',
                    'hire', 'hiring', 'looking for', 'need help'
                ],
                'low': []
            },
            'authority': {
                'high': [],  # Numeric thresholds
                'medium': [],
                'low': []
            },
            'recency': {
                'high': [],  # Time-based
                'medium': [],
                'low': []
            },
            'data_quality': {
                'high': [],
                'medium': [],
                'low': []
            }
        }

    async def calculate_score(self, url_results: List[Dict[str, Any]]) -> Tuple[int, str]:
        """Calculate deterministic lead score.

        Args:
            url_results: List of URL processing results

        Returns:
            Tuple of (score 0-100, notes explaining score factors)
        """
        try:
            # Filter successful results only
            successful_results = [r for r in url_results if r.get('status') == 'OK']

            if not successful_results:
                return 0, "No successful data collection"

            # Calculate each scoring dimension
            relevance_score = self._score_relevance(successful_results)
            intent_score = self._score_purchase_intent(successful_results)
            authority_score = self._score_authority(successful_results)
            recency_score = self._score_recency(successful_results)
            quality_score = self._score_data_quality(successful_results, url_results)

            # Apply weights and calculate final score
            final_score = (
                (relevance_score * self.weights['relevance']) +
                (intent_score * self.weights['purchase_intent']) +
                (authority_score * self.weights['authority']) +
                (recency_score * self.weights['recency']) +
                (quality_score * self.weights['data_quality'])
            ) / 100

            # Round to integer
            final_score = min(100, max(0, round(final_score)))

            # Generate score notes
            notes = self._generate_score_notes(
                relevance_score, intent_score, authority_score,
                recency_score, quality_score, successful_results
            )

            logger.debug(f"Calculated lead score: {final_score}")
            return final_score, notes

        except Exception as e:
            logger.error(f"Error calculating lead score: {e}")
            return 0, f"Scoring error: {str(e)}"

    def _score_relevance(self, results: List[Dict[str, Any]]) -> int:
        """Score relevance to our services (0-100).

        Args:
            results: Successful URL results

        Returns:
            Relevance score
        """
        all_content = self._extract_all_content(results)
        content_lower = all_content.lower()

        high_relevance_matches = sum(
            1 for keyword in self.scoring_patterns['relevance']['high']
            if keyword in content_lower
        )

        medium_relevance_matches = sum(
            1 for keyword in self.scoring_patterns['relevance']['medium']
            if keyword in content_lower
        )

        # Score based on matches
        score = 0
        if high_relevance_matches >= 3:
            score = 90
        elif high_relevance_matches >= 2:
            score = 75
        elif high_relevance_matches >= 1:
            score = 60
        elif medium_relevance_matches >= 2:
            score = 40
        elif medium_relevance_matches >= 1:
            score = 25
        else:
            score = 10

        return min(100, score)

    def _score_purchase_intent(self, results: List[Dict[str, Any]]) -> int:
        """Score purchase intent signals (0-100).

        Args:
            results: Successful URL results

        Returns:
            Purchase intent score
        """
        all_content = self._extract_all_content(results)
        content_lower = all_content.lower()

        # Check for high-intent signals
        high_intent_matches = sum(
            1 for keyword in self.scoring_patterns['purchase_intent']['high']
            if keyword in content_lower
        )

        medium_intent_matches = sum(
            1 for keyword in self.scoring_patterns['purchase_intent']['medium']
            if keyword in content_lower
        )

        # Check for specific high-value signals
        has_pricing = any(word in content_lower for word in ['pricing', 'plans', 'cost'])
        has_contact_sales = any(word in content_lower for word in ['contact sales', 'sales team'])
        has_trial = any(word in content_lower for word in ['free trial', 'trial', 'demo'])
        is_hiring = 'hiring' in content_lower or 'careers' in content_lower

        score = 0
        if has_contact_sales or has_pricing:
            score = 90
        elif has_trial:
            score = 75
        elif high_intent_matches >= 2:
            score = 65
        elif high_intent_matches >= 1:
            score = 50
        elif is_hiring:
            score = 45
        elif medium_intent_matches >= 2:
            score = 35
        elif medium_intent_matches >= 1:
            score = 20
        else:
            score = 5

        return min(100, score)

    def _score_authority(self, results: List[Dict[str, Any]]) -> int:
        """Score authority/size indicators (0-100).

        Args:
            results: Successful URL results

        Returns:
            Authority score
        """
        score = 0
        content = self._extract_all_content(results)

        # Social media metrics
        followers = self._extract_follower_count(content)
        if followers:
            if followers >= 100000:
                score = max(score, 90)
            elif followers >= 10000:
                score = max(score, 75)
            elif followers >= 1000:
                score = max(score, 60)
            elif followers >= 100:
                score = max(score, 40)

        # GitHub metrics
        stars = self._extract_github_stars(content)
        if stars:
            if stars >= 1000:
                score = max(score, 85)
            elif stars >= 100:
                score = max(score, 70)
            elif stars >= 50:
                score = max(score, 55)
            elif stars >= 10:
                score = max(score, 35)

        # Business size indicators
        if any(indicator in content.lower() for indicator in [
            'enterprise', 'corporation', 'inc.', 'ltd.', 'llc'
        ]):
            score = max(score, 60)

        # Team size indicators
        if any(indicator in content.lower() for indicator in [
            'team of', 'employees', 'staff', 'founded'
        ]):
            score = max(score, 45)

        # Default for any professional presence
        if score == 0 and len(results) > 0:
            score = 25

        return min(100, score)

    def _score_recency(self, results: List[Dict[str, Any]]) -> int:
        """Score recent activity (0-100).

        Args:
            results: Successful URL results

        Returns:
            Recency score
        """
        content = self._extract_all_content(results)
        content_lower = content.lower()

        # Look for recency indicators
        recent_indicators = [
            'recent', 'latest', 'new', 'updated', 'last week',
            'last month', 'yesterday', 'today', '2024', '2025'
        ]

        recent_matches = sum(
            1 for indicator in recent_indicators
            if indicator in content_lower
        )

        # Social media activity indicators
        has_recent_posts = any(phrase in content_lower for phrase in [
            'recent tweet', 'recent video', 'recent post', 'latest video'
        ])

        # News/blog activity
        has_recent_content = any(phrase in content_lower for phrase in [
            'recent:', 'published:', 'updated:'
        ])

        score = 0
        if has_recent_posts:
            score = 85
        elif has_recent_content:
            score = 70
        elif recent_matches >= 3:
            score = 60
        elif recent_matches >= 2:
            score = 45
        elif recent_matches >= 1:
            score = 30
        else:
            score = 10

        return min(100, score)

    def _score_data_quality(self, successful_results: List[Dict[str, Any]], all_results: List[Dict[str, Any]]) -> int:
        """Score data quality and consistency (0-100).

        Args:
            successful_results: Successful URL results
            all_results: All URL results (including failed)

        Returns:
            Data quality score
        """
        if not all_results:
            return 0

        # Success rate
        success_rate = len(successful_results) / len(all_results)

        # Number of data sources
        num_sources = len(successful_results)

        # Content richness (average key points per source)
        total_key_points = sum(
            len(result.get('key_points', []))
            for result in successful_results
        )
        avg_key_points = total_key_points / max(1, len(successful_results))

        # Calculate quality score
        score = 0

        # Success rate component (40% of score)
        score += success_rate * 40

        # Data source diversity (30% of score)
        if num_sources >= 3:
            score += 30
        elif num_sources == 2:
            score += 20
        elif num_sources == 1:
            score += 10

        # Content richness (30% of score)
        if avg_key_points >= 4:
            score += 30
        elif avg_key_points >= 3:
            score += 25
        elif avg_key_points >= 2:
            score += 20
        elif avg_key_points >= 1:
            score += 15
        else:
            score += 5

        return min(100, round(score))

    def _extract_all_content(self, results: List[Dict[str, Any]]) -> str:
        """Extract all text content from results.

        Args:
            results: URL results

        Returns:
            Combined text content
        """
        content_parts = []

        for result in results:
            # Add key points
            key_points = result.get('key_points', [])
            content_parts.extend(key_points)

            # Add signals
            signals = result.get('signals', [])
            content_parts.extend(signals)

        return ' '.join(content_parts)

    def _extract_follower_count(self, content: str) -> int:
        """Extract follower count from content.

        Args:
            content: Text content

        Returns:
            Follower count or 0 if not found
        """
        import re

        # Look for follower patterns
        patterns = [
            r'(\d+[,.]?\d*)[kKmM]?\s*followers',
            r'followers:\s*(\d+[,.]?\d*)[kKmM]?',
            r'(\d+[,.]?\d*)[kKmM]?\s*followers'
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                number_str = match.group(1).replace(',', '').replace('.', '')
                try:
                    number = float(number_str)
                    # Handle K/M suffixes
                    if 'k' in match.group(0).lower():
                        number *= 1000
                    elif 'm' in match.group(0).lower():
                        number *= 1000000
                    return int(number)
                except ValueError:
                    continue

        return 0

    def _extract_github_stars(self, content: str) -> int:
        """Extract GitHub star count from content.

        Args:
            content: Text content

        Returns:
            Star count or 0 if not found
        """
        import re

        # Look for star patterns
        patterns = [
            r'(\d+[,.]?\d*)\s*stars',
            r'stars:\s*(\d+[,.]?\d*)',
            r'(\d+[,.]?\d*)\s*⭐'
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                number_str = match.group(1).replace(',', '').replace('.', '')
                try:
                    return int(float(number_str))
                except ValueError:
                    continue

        return 0

    def _generate_score_notes(
        self,
        relevance_score: int,
        intent_score: int,
        authority_score: int,
        recency_score: int,
        quality_score: int,
        results: List[Dict[str, Any]]
    ) -> str:
        """Generate explanatory notes for the score.

        Args:
            relevance_score: Relevance component score
            intent_score: Purchase intent component score
            authority_score: Authority component score
            recency_score: Recency component score
            quality_score: Data quality component score
            results: Successful results

        Returns:
            Score explanation notes
        """
        notes = []

        # Relevance factors
        if relevance_score >= 75:
            notes.append("High service relevance")
        elif relevance_score >= 50:
            notes.append("Moderate service relevance")

        # Purchase intent factors
        content = self._extract_all_content(results).lower()
        if 'pricing' in content or 'plans' in content:
            notes.append("Pricing page found")
        if 'contact sales' in content:
            notes.append("Sales contact available")
        if 'hiring' in content:
            notes.append("Currently hiring")

        # Authority factors
        followers = self._extract_follower_count(content)
        if followers >= 10000:
            notes.append(f"Large following ({followers:,})")
        elif followers >= 1000:
            notes.append(f"Good following ({followers:,})")

        stars = self._extract_github_stars(content)
        if stars >= 100:
            notes.append(f"Popular projects ({stars}+ stars)")

        # Recency factors
        if any('recent' in str(result).lower() for result in results):
            notes.append("Recent activity detected")

        # Data quality factors
        if len(results) >= 3:
            notes.append(f"Multiple data sources ({len(results)})")

        # Limit to 5 notes
        if len(notes) > 5:
            notes = notes[:5]

        return "; ".join(notes) if notes else "Basic lead profile"