"""
Tests for deterministic scoring system.

Ensures scoring is consistent and reproducible for the same inputs,
and tests the weighted rubric calculations.
"""

import pytest
from utils.scoring import LeadScorer


class TestScoringDeterminism:
    """Test deterministic lead scoring system."""

    def setup_method(self):
        """Setup for each test."""
        self.scorer = LeadScorer()

    @pytest.mark.asyncio
    async def test_scoring_determinism(self):
        """Test that scoring is deterministic for identical inputs."""
        # Sample URL results
        sample_results = [
            {
                'source': 'example.com',
                'url': 'https://example.com',
                'key_points': [
                    'Title: SaaS Platform for Marketing',
                    'Description: Cloud-based analytics solution',
                    'Features: API integration, automation tools'
                ],
                'signals': [
                    'Has pricing content',
                    'Contact sales available',
                    'Technology-focused company'
                ],
                'status': 'OK',
                'last_checked': '2024-01-01T12:00:00Z'
            }
        ]

        # Calculate score multiple times
        scores = []
        notes_list = []

        for _ in range(5):
            score, notes = await self.scorer.calculate_score(sample_results)
            scores.append(score)
            notes_list.append(notes)

        # All scores should be identical
        assert len(set(scores)) == 1, f"Scores varied: {scores}"
        assert len(set(notes_list)) == 1, f"Notes varied: {notes_list}"

    @pytest.mark.asyncio
    async def test_scoring_weights_sum_to_100(self):
        """Test that scoring weights sum to 100."""
        total_weight = sum(self.scorer.weights.values())
        assert total_weight == 100, f"Weights sum to {total_weight}, not 100"

    @pytest.mark.asyncio
    async def test_relevance_scoring(self):
        """Test relevance scoring component."""
        # High relevance case
        high_relevance_results = [{
            'key_points': ['SaaS platform', 'API integration', 'cloud automation'],
            'signals': ['Technology platform', 'Software solution'],
            'status': 'OK'
        }]

        relevance_score = self.scorer._score_relevance(high_relevance_results)
        assert relevance_score >= 75, f"High relevance score too low: {relevance_score}"

        # Low relevance case
        low_relevance_results = [{
            'key_points': ['Restaurant menu', 'Food delivery'],
            'signals': ['Local business'],
            'status': 'OK'
        }]

        relevance_score = self.scorer._score_relevance(low_relevance_results)
        assert relevance_score <= 40, f"Low relevance score too high: {relevance_score}"

    @pytest.mark.asyncio
    async def test_purchase_intent_scoring(self):
        """Test purchase intent scoring component."""
        # High intent case
        high_intent_results = [{
            'key_points': ['Pricing plans available', 'Contact sales team'],
            'signals': ['Has pricing content', 'Free trial available'],
            'status': 'OK'
        }]

        intent_score = self.scorer._score_purchase_intent(high_intent_results)
        assert intent_score >= 80, f"High intent score too low: {intent_score}"

        # Low intent case
        low_intent_results = [{
            'key_points': ['Company blog', 'About us page'],
            'signals': ['Informational content'],
            'status': 'OK'
        }]

        intent_score = self.scorer._score_purchase_intent(low_intent_results)
        assert intent_score <= 30, f"Low intent score too high: {intent_score}"

    @pytest.mark.asyncio
    async def test_authority_scoring(self):
        """Test authority/size scoring component."""
        # High authority case
        high_authority_results = [{
            'key_points': ['Followers: 50,000', 'Enterprise company'],
            'signals': ['Large following', 'Corporate presence'],
            'status': 'OK'
        }]

        authority_score = self.scorer._score_authority(high_authority_results)
        assert authority_score >= 70, f"High authority score too low: {authority_score}"

        # Low authority case
        low_authority_results = [{
            'key_points': ['Personal blog', 'Individual contributor'],
            'signals': ['Small presence'],
            'status': 'OK'
        }]

        authority_score = self.scorer._score_authority(low_authority_results)
        assert authority_score <= 50, f"Low authority score too high: {authority_score}"

    @pytest.mark.asyncio
    async def test_recency_scoring(self):
        """Test recency scoring component."""
        # Recent activity case
        recent_results = [{
            'key_points': ['Recent tweet: New product launch', 'Updated: 2024'],
            'signals': ['Recent activity detected'],
            'status': 'OK'
        }]

        recency_score = self.scorer._score_recency(recent_results)
        assert recency_score >= 60, f"Recent activity score too low: {recency_score}"

        # Old activity case
        old_results = [{
            'key_points': ['Old blog post', 'Last updated: 2020'],
            'signals': ['Inactive presence'],
            'status': 'OK'
        }]

        recency_score = self.scorer._score_recency(old_results)
        assert recency_score <= 40, f"Old activity score too high: {recency_score}"

    @pytest.mark.asyncio
    async def test_data_quality_scoring(self):
        """Test data quality scoring component."""
        # High quality case (multiple successful sources)
        successful_results = [
            {'key_points': ['Point 1', 'Point 2', 'Point 3'], 'status': 'OK'},
            {'key_points': ['Point A', 'Point B'], 'status': 'OK'},
            {'key_points': ['Point X', 'Point Y', 'Point Z'], 'status': 'OK'}
        ]
        all_results = successful_results.copy()

        quality_score = self.scorer._score_data_quality(successful_results, all_results)
        assert quality_score >= 80, f"High quality score too low: {quality_score}"

        # Low quality case (mostly failed sources)
        failed_results = [
            {'key_points': ['Point 1'], 'status': 'OK'}
        ]
        all_with_failures = failed_results + [
            {'status': 'ERROR'}, {'status': 'SKIPPED_TOS'}, {'status': 'ERROR'}
        ]

        quality_score = self.scorer._score_data_quality(failed_results, all_with_failures)
        assert quality_score <= 50, f"Low quality score too high: {quality_score}"

    @pytest.mark.asyncio
    async def test_follower_count_extraction(self):
        """Test extraction of follower counts from content."""
        test_cases = [
            ('Followers: 10,000', 10000),
            ('10K followers', 10000),
            ('1.5M followers', 1500000),
            ('500 followers', 500),
            ('No follower info', 0)
        ]

        for content, expected in test_cases:
            extracted = self.scorer._extract_follower_count(content)
            assert extracted == expected, f"Failed for '{content}': got {extracted}, expected {expected}"

    @pytest.mark.asyncio
    async def test_github_stars_extraction(self):
        """Test extraction of GitHub star counts from content."""
        test_cases = [
            ('1,500 stars', 1500),
            ('50 stars', 50),
            ('⭐ 250', 250),
            ('Popular projects (1000+ stars)', 1000),
            ('No star info', 0)
        ]

        for content, expected in test_cases:
            extracted = self.scorer._extract_github_stars(content)
            assert extracted == expected, f"Failed for '{content}': got {extracted}, expected {expected}"

    @pytest.mark.asyncio
    async def test_score_range_validation(self):
        """Test that scores always fall within 0-100 range."""
        # Test various input scenarios
        test_scenarios = [
            [],  # Empty results
            [{'status': 'ERROR'}],  # Error only
            [{'status': 'SKIPPED_TOS'}],  # Skipped only
            [{  # Minimal success
                'key_points': ['Basic info'],
                'signals': [],
                'status': 'OK'
            }],
            [{  # Maximum signals
                'key_points': ['SaaS', 'API', 'pricing', 'enterprise', 'automation'] * 5,
                'signals': ['Pricing available', 'Contact sales', 'Recent activity'] * 5,
                'status': 'OK'
            }]
        ]

        for scenario in test_scenarios:
            score, notes = await self.scorer.calculate_score(scenario)
            assert 0 <= score <= 100, f"Score {score} out of range for scenario: {scenario}"
            assert isinstance(notes, str), f"Notes should be string, got {type(notes)}"

    @pytest.mark.asyncio
    async def test_score_notes_generation(self):
        """Test generation of explanatory score notes."""
        results = [{
            'key_points': ['SaaS platform', 'Pricing page found', 'Recent activity'],
            'signals': ['High service relevance', 'Contact sales available', 'Popular developer'],
            'status': 'OK'
        }]

        score, notes = await self.scorer.calculate_score(results)

        # Notes should contain relevant factors
        assert isinstance(notes, str)
        assert len(notes) > 0
        # Should mention key scoring factors
        factors_mentioned = any(keyword in notes.lower() for keyword in [
            'pricing', 'relevance', 'sales', 'popular', 'activity'
        ])
        assert factors_mentioned, f"Notes don't mention key factors: {notes}"

    @pytest.mark.asyncio
    async def test_weighted_score_calculation(self):
        """Test that final score properly applies weights."""
        # Create controlled results to test weighting
        results = [{
            'key_points': ['SaaS platform'],  # Moderate relevance
            'signals': ['Pricing available'],  # High intent
            'status': 'OK'
        }]

        score, notes = await self.scorer.calculate_score(results)

        # Manually calculate expected ranges based on weights
        # Relevance (30%), Intent (25%), Authority (20%), Recency (15%), Quality (10%)
        # This is more of a sanity check that weighting is applied

        assert 0 <= score <= 100
        assert isinstance(score, int)

    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with None/empty values
        edge_cases = [
            None,
            [],
            [None],
            [{}],
            [{'status': None}],
            [{'key_points': None, 'signals': None, 'status': 'OK'}]
        ]

        for case in edge_cases:
            try:
                score, notes = await self.scorer.calculate_score(case or [])
                assert 0 <= score <= 100
                assert isinstance(notes, str)
            except Exception as e:
                pytest.fail(f"Failed on edge case {case}: {e}")

    @pytest.mark.asyncio
    async def test_scoring_consistency_across_sessions(self):
        """Test that scoring is consistent across different scorer instances."""
        results = [{
            'key_points': ['SaaS platform', 'API integration'],
            'signals': ['Technology focused', 'Pricing available'],
            'status': 'OK'
        }]

        # Create multiple scorer instances
        scorers = [LeadScorer() for _ in range(3)]
        scores = []

        for scorer in scorers:
            score, notes = await scorer.calculate_score(results)
            scores.append(score)

        # All scores should be identical
        assert len(set(scores)) == 1, f"Scores varied across instances: {scores}"

    @pytest.mark.asyncio
    async def test_mixed_status_handling(self):
        """Test handling of mixed success/failure statuses."""
        mixed_results = [
            {
                'key_points': ['SaaS platform'],
                'signals': ['Technology company'],
                'status': 'OK'
            },
            {
                'key_points': ['Error occurred'],
                'signals': [],
                'status': 'ERROR'
            },
            {
                'key_points': ['Skipped due to ToS'],
                'signals': [],
                'status': 'SKIPPED_TOS'
            }
        ]

        score, notes = await self.scorer.calculate_score(mixed_results)

        # Should only score successful results
        assert score > 0, "Should have positive score for successful result"
        assert score < 100, "Should be penalized for failed results"

    @pytest.mark.asyncio
    async def test_comprehensive_high_score_scenario(self):
        """Test a comprehensive scenario that should yield a high score."""
        high_score_results = [
            {
                'key_points': [
                    'SaaS automation platform',
                    'API integration capabilities',
                    'Pricing: Enterprise plans available',
                    'Recent activity: Product launch 2024',
                    'Team: 50+ engineers'
                ],
                'signals': [
                    'High service relevance',
                    'Pricing page found',
                    'Contact sales available',
                    'Recent activity detected',
                    'Large team size'
                ],
                'status': 'OK'
            },
            {
                'key_points': [
                    'GitHub: 5000+ stars',
                    'Followers: 25,000',
                    'Active contributor'
                ],
                'signals': [
                    'Popular projects',
                    'Large following',
                    'Technical authority'
                ],
                'status': 'OK'
            }
        ]

        score, notes = await self.scorer.calculate_score(high_score_results)

        # Should achieve high score
        assert score >= 75, f"High-quality scenario scored too low: {score}"

        # Notes should reflect high scoring factors
        assert 'pricing' in notes.lower() or 'relevance' in notes.lower()

    @pytest.mark.asyncio
    async def test_comprehensive_low_score_scenario(self):
        """Test a comprehensive scenario that should yield a low score."""
        low_score_results = [
            {
                'key_points': [
                    'Personal blog',
                    'Hobby project',
                    'Last updated: 2020'
                ],
                'signals': [
                    'Individual contributor',
                    'Inactive presence'
                ],
                'status': 'OK'
            }
        ]

        score, notes = await self.scorer.calculate_score(low_score_results)

        # Should achieve low score
        assert score <= 30, f"Low-quality scenario scored too high: {score}"