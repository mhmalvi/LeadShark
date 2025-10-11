#!/usr/bin/env python3
"""
Cold Outreach Engine
Extracts personalization data and generates cold email components
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ColdOutreachEngine:
    """
    Extracts personalization signals and generates cold email components:
    - Recent activity detection
    - Pain point extraction
    - Trigger event identification
    - Social proof extraction
    - Subject line generation (3 variants)
    - Opening line generation
    - Value proposition matching
    - CTA generation
    """

    def __init__(self, ai_client=None):
        """
        Initialize cold outreach engine
        Args:
            ai_client: Optional AI client (OpenAI/Anthropic) for advanced analysis
        """
        self.ai_client = ai_client

        # Recent activity keywords
        self.recent_activity_keywords = [
            'recently', 'just', 'announced', 'announces', 'launches', 'launched',
            'new', 'expanding', 'expanded', 'growing', 'scaling', 'hiring',
            'introducing', 'released', 'unveils', 'unveiled'
        ]

        # Trigger event patterns
        self.trigger_patterns = {
            'funding': ['raised', 'funding', 'series', 'investment', 'capital'],
            'hiring': ['hiring', 'recruiting', 'looking for', 'job opening', 'careers'],
            'expansion': ['expanding', 'new office', 'new location', 'growing', 'scaling'],
            'product_launch': ['launched', 'launches', 'introducing', 'new product', 'new service'],
            'partnership': ['partners with', 'partnership', 'collaboration', 'alliance'],
            'award': ['awarded', 'wins', 'recognized', 'named', 'top']
        }

        # Social proof patterns
        self.social_proof_patterns = {
            'years_in_business': r'(?:since|established|founded in)\s+(\d{4})',
            'client_count': r'(\d+[\+]?)\s+(?:clients|customers|businesses)',
            'followers': r'(\d{1,3}(?:,\d{3})*)\s+(?:followers|likes)',
            'testimonials': r'(?:testimonial|review|feedback)'
        }

    def extract_personalization_data(
        self,
        scraped_content: str,
        company_name: str,
        person_name: str,
        title: str
    ) -> Dict:
        """
        Extract all personalization data from scraped content
        Returns comprehensive personalization dict
        """
        result = {
            'recent_activity': self._extract_recent_activity(scraped_content),
            'trigger_events': self._extract_trigger_events(scraped_content),
            'social_proof': self._extract_social_proof(scraped_content),
            'pain_points': [],  # Will be populated by AI if available
            'personalization_hook': ''
        }

        # Extract AI-powered pain points if client available
        if self.ai_client:
            result['pain_points'] = self._extract_pain_points_ai(
                scraped_content,
                company_name,
                title
            )

        # Generate personalization hook
        result['personalization_hook'] = self._generate_personalization_hook(
            person_name,
            company_name,
            result['recent_activity'],
            result['trigger_events']
        )

        return result

    def _extract_recent_activity(self, content: str) -> str:
        """
        Extract recent activity signals from content
        Returns the most relevant recent activity mention
        """
        if not content:
            return ""

        content_lower = content.lower()

        # Look for sentences containing recent activity keywords
        sentences = re.split(r'[.!?]\s+', content)

        recent_activities = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in self.recent_activity_keywords):
                # Clean and truncate sentence
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 200:
                    clean_sentence = clean_sentence[:200] + '...'
                recent_activities.append(clean_sentence)

        # Return the first relevant activity found
        return recent_activities[0] if recent_activities else ""

    def _extract_trigger_events(self, content: str) -> List[Dict[str, str]]:
        """
        Extract trigger events from content
        Returns list of {type, description} dicts
        """
        if not content:
            return []

        content_lower = content.lower()
        trigger_events = []

        sentences = re.split(r'[.!?]\s+', content)

        for trigger_type, keywords in self.trigger_patterns.items():
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(keyword in sentence_lower for keyword in keywords):
                    trigger_events.append({
                        'type': trigger_type,
                        'description': sentence.strip()[:200]
                    })
                    break  # One event per type

        return trigger_events

    def _extract_social_proof(self, content: str) -> Dict:
        """
        Extract social proof signals from content
        Returns dict with years_in_business, client_count, followers, testimonials
        """
        if not content:
            return {}

        social_proof = {}

        # Extract years in business
        years_match = re.search(self.social_proof_patterns['years_in_business'], content, re.IGNORECASE)
        if years_match:
            founded_year = int(years_match.group(1))
            current_year = datetime.now().year
            years_in_business = current_year - founded_year
            social_proof['years_in_business'] = years_in_business

        # Extract client count
        client_match = re.search(self.social_proof_patterns['client_count'], content, re.IGNORECASE)
        if client_match:
            social_proof['client_count'] = client_match.group(1)

        # Extract followers/likes
        follower_match = re.search(self.social_proof_patterns['followers'], content, re.IGNORECASE)
        if follower_match:
            social_proof['followers'] = follower_match.group(1)

        # Check for testimonials
        if re.search(self.social_proof_patterns['testimonials'], content, re.IGNORECASE):
            social_proof['has_testimonials'] = True

        return social_proof

    def _extract_pain_points_ai(
        self,
        content: str,
        company_name: str,
        industry: str
    ) -> List[str]:
        """
        Use AI to extract pain points from content
        Returns list of 3 pain points
        """
        if not self.ai_client or not content:
            return []

        # Limit content to 3000 chars for API efficiency
        content_truncated = content[:3000]

        prompt = f"""Based on the following content about {company_name} (a {industry} company), identify 3 specific pain points or challenges they might be facing.

Content:
{content_truncated}

Return ONLY a JSON array of 3 pain points, each as a short string (10-15 words max).
Example format: ["Challenge 1", "Challenge 2", "Challenge 3"]
"""

        try:
            # Call AI client (OpenAI or Anthropic)
            response = self._call_ai_client(prompt)

            # Parse JSON response
            pain_points = json.loads(response)

            # Validate it's a list of strings
            if isinstance(pain_points, list) and len(pain_points) <= 3:
                return [str(p)[:100] for p in pain_points]  # Truncate each to 100 chars

        except Exception as e:
            # If AI fails, return empty list
            pass

        return []

    def _generate_personalization_hook(
        self,
        person_name: str,
        company_name: str,
        recent_activity: str,
        trigger_events: List[Dict]
    ) -> str:
        """
        Generate personalized opening hook based on available signals
        """
        hooks = []

        # Hook based on recent activity
        if recent_activity:
            # Extract key phrase from activity
            activity_lower = recent_activity.lower()
            if 'expand' in activity_lower:
                hooks.append(f"Noticed {company_name} is expanding - congrats on the growth!")
            elif 'launch' in activity_lower:
                hooks.append(f"Saw {company_name}'s recent launch - exciting times!")
            elif 'hir' in activity_lower:
                hooks.append(f"Noticed {company_name} is hiring - growing fast!")
            else:
                hooks.append(f"Following {company_name}'s recent developments")

        # Hook based on trigger events
        if trigger_events:
            top_event = trigger_events[0]
            event_type = top_event['type']

            if event_type == 'funding':
                hooks.append(f"Congratulations on the recent funding round!")
            elif event_type == 'product_launch':
                hooks.append(f"Impressed by {company_name}'s new product launch")
            elif event_type == 'partnership':
                hooks.append(f"Saw the exciting partnership announcement")
            elif event_type == 'award':
                hooks.append(f"Congratulations on the recent recognition!")

        # Default hook if no signals found
        if not hooks:
            hooks.append(f"Been following {company_name}'s work")

        return hooks[0]

    def generate_subject_lines(
        self,
        person_name: str,
        company_name: str,
        personalization_data: Dict,
        product_category: str = "solution"
    ) -> List[str]:
        """
        Generate 3 subject line variants
        """
        first_name = person_name.split()[0] if person_name else "there"

        subject_lines = []

        # Variant 1: Question-based with pain point
        pain_points = personalization_data.get('pain_points', [])
        if pain_points:
            pain_point_short = pain_points[0][:50]
            subject_lines.append(f"Quick question about {company_name}'s {pain_point_short}?")
        else:
            subject_lines.append(f"Quick question about {company_name}'s workflow")

        # Variant 2: Recent activity hook
        recent_activity = personalization_data.get('recent_activity', '')
        trigger_events = personalization_data.get('trigger_events', [])

        if trigger_events:
            event_type = trigger_events[0]['type']
            if event_type == 'expansion':
                subject_lines.append(f"{first_name} - scaling {company_name}?")
            elif event_type == 'hiring':
                subject_lines.append(f"{first_name} - hiring at {company_name}?")
            else:
                subject_lines.append(f"Saw {company_name}'s latest update")
        elif 'expand' in recent_activity.lower():
            subject_lines.append(f"Saw {company_name}'s expansion")
        else:
            subject_lines.append(f"{first_name} - thoughts on {product_category} for {company_name}")

        # Variant 3: Value-focused
        subject_lines.append(f"Helping {company_name} save 10+ hours/week")

        return subject_lines[:3]

    def generate_opening_line(
        self,
        person_name: str,
        company_name: str,
        personalization_data: Dict
    ) -> str:
        """
        Generate personalized opening line (first sentence of email)
        """
        first_name = person_name.split()[0] if person_name else "there"

        # Use personalization hook if available
        hook = personalization_data.get('personalization_hook', '')
        if hook:
            return f"{first_name}, {hook.lower()}"

        # Fallback generic opening
        return f"{first_name}, I've been following {company_name}'s work"

    def generate_value_prop_match(
        self,
        company_name: str,
        industry: str,
        pain_points: List[str]
    ) -> str:
        """
        Generate value proposition matched to company's needs
        """
        if not industry:
            industry = "your industry"

        # Match value prop to pain points
        if pain_points:
            pain_point = pain_points[0]
            return f"Companies like {company_name} typically see significant improvements when addressing {pain_point.lower()}"

        # Generic value prop by industry
        industry_lower = industry.lower()

        if 'marketing' in industry_lower or 'agency' in industry_lower:
            return f"Marketing agencies like {company_name} typically save 10+ hours/week with automated client reporting"
        elif 'software' in industry_lower or 'tech' in industry_lower:
            return f"Tech companies like {company_name} typically see 40% faster deployment with streamlined workflows"
        elif 'consulting' in industry_lower:
            return f"Consulting firms like {company_name} typically increase client retention by 25% with better project tracking"
        else:
            return f"Companies like {company_name} typically see measurable ROI within 30 days"

    def generate_cta(self, company_name: str = "", meeting_type: str = "quick call") -> str:
        """
        Generate call-to-action
        """
        if company_name:
            cta_templates = [
                f"Worth a quick 15-min {meeting_type} to see if this could help {company_name}?",
                f"Open to a brief {meeting_type} to explore this?",
                f"Would you be interested in a {meeting_type} to discuss?"
            ]
        else:
            cta_templates = [
                f"Worth a quick 15-min {meeting_type} to explore this?",
                f"Open to a brief {meeting_type}?",
                f"Would you be interested in a {meeting_type} to discuss?"
            ]

        return cta_templates[0]  # Return first variant

    def _call_ai_client(self, prompt: str) -> str:
        """
        Call AI client (OpenAI or Anthropic) with prompt
        Returns response text
        """
        # This would be implemented based on which AI client is available
        # For now, return empty string
        return "[]"

    def generate_complete_email_components(
        self,
        person_name: str,
        company_name: str,
        industry: str,
        scraped_content: str,
        product_category: str = "solution"
    ) -> Dict:
        """
        Generate all cold email components in one call
        Returns complete dict ready for columns
        """
        # Extract personalization data
        personalization_data = self.extract_personalization_data(
            scraped_content,
            company_name,
            person_name,
            industry
        )

        # Generate all components
        subject_lines = self.generate_subject_lines(
            person_name,
            company_name,
            personalization_data,
            product_category
        )

        opening_line = self.generate_opening_line(
            person_name,
            company_name,
            personalization_data
        )

        value_prop = self.generate_value_prop_match(
            company_name,
            industry,
            personalization_data.get('pain_points', [])
        )

        cta = self.generate_cta(company_name)

        # Format trigger events for column
        trigger_events_str = ""
        if personalization_data.get('trigger_events'):
            events = personalization_data['trigger_events']
            trigger_events_str = " | ".join([f"{e['type']}: {e['description'][:100]}" for e in events])

        # Format social proof for column
        social_proof = personalization_data.get('social_proof', {})
        social_proof_str = ""
        if social_proof:
            parts = []
            if 'years_in_business' in social_proof:
                parts.append(f"{social_proof['years_in_business']} years in business")
            if 'client_count' in social_proof:
                parts.append(f"{social_proof['client_count']} clients")
            if 'followers' in social_proof:
                parts.append(f"{social_proof['followers']} followers")
            social_proof_str = " | ".join(parts)

        return {
            # Personalization data
            'recent_activity': personalization_data['recent_activity'],
            'pain_points': " | ".join(personalization_data.get('pain_points', [])),
            'personalization_hook': personalization_data['personalization_hook'],
            'social_proof': social_proof_str,
            'trigger_event': trigger_events_str,

            # Email components
            'subject_line_1': subject_lines[0] if len(subject_lines) > 0 else '',
            'subject_line_2': subject_lines[1] if len(subject_lines) > 1 else '',
            'subject_line_3': subject_lines[2] if len(subject_lines) > 2 else '',
            'opening_line': opening_line,
            'value_prop_match': value_prop,
            'suggested_cta': cta
        }


# Test function
if __name__ == "__main__":
    engine = ColdOutreachEngine()

    # Test data
    test_content = """
    Ahead Creative is a full-service marketing agency based in Melbourne, Australia.
    Founded in 2015, we've helped over 200 clients grow their brands.
    We recently expanded into TV spot production and are hiring two new creative directors.
    Our work has been featured in AdWeek and we were named Top Agency of 2023.
    """

    result = engine.generate_complete_email_components(
        person_name="Lorenzo Smith",
        company_name="Ahead Creative",
        industry="Marketing Agency",
        scraped_content=test_content,
        product_category="workflow automation"
    )

    print("Cold Outreach Engine Test\n")
    print("=" * 60)
    for key, value in result.items():
        print(f"{key}: {value}")
