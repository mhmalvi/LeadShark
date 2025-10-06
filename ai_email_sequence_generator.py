#!/usr/bin/env python3
"""
AI-Powered Email Sequence Generator
Creates personalized multi-touch email sequences using OpenAI GPT
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIEmailSequenceGenerator:
    """
    Generates complete email sequences using AI based on comprehensive lead data

    Features:
    - 5-email sequence (Initial, Follow-up 1-3, Break-up)
    - Personalized to all row data (LinkedIn, company, activity, pain points)
    - AI-powered content generation using OpenAI GPT
    - Multiple tone variations
    - Industry-specific messaging
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize email sequence generator

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY', '')

        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY env var.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

        # Email sequence structure (5-email cadence)
        self.sequence_structure = {
            'email_1': {
                'name': 'Initial Outreach',
                'goal': 'Introduce yourself and establish relevance',
                'timing': 'Day 1',
                'tone': 'Professional, curious, value-focused'
            },
            'email_2': {
                'name': 'Value Add Follow-up',
                'goal': 'Provide value without asking for anything',
                'timing': 'Day 3',
                'tone': 'Helpful, educational, non-pushy'
            },
            'email_3': {
                'name': 'Case Study/Social Proof',
                'goal': 'Show results with similar companies',
                'timing': 'Day 7',
                'tone': 'Data-driven, proof-focused'
            },
            'email_4': {
                'name': 'Direct Ask',
                'goal': 'Clear call-to-action for meeting',
                'timing': 'Day 10',
                'tone': 'Direct, confident, respectful'
            },
            'email_5': {
                'name': 'Break-up Email',
                'goal': 'Final attempt with permission to close loop',
                'timing': 'Day 14',
                'tone': 'Humble, understanding, door-open'
            }
        }

    def extract_personalization_hooks(self, lead_data: Dict) -> Dict[str, List[str]]:
        """
        Extract specific personalization hooks from scraped content

        Returns dict with:
        - specific_projects: Mentioned projects, campaigns, clients
        - recent_news: Recent announcements, launches, expansions
        - tech_stack: Technologies/tools mentioned
        - achievements: Awards, milestones, growth metrics
        - team_info: Hiring, team size, key people
        """
        hooks = {
            'specific_projects': [],
            'recent_news': [],
            'tech_stack': [],
            'achievements': [],
            'team_info': []
        }

        # Get all available text content
        content_sources = []

        # Add scraped content if available
        scraped_content = lead_data.get('scraped_content', '')
        if scraped_content:
            content_sources.append(scraped_content)

        # Add website summary if available
        website_summary = lead_data.get('website_summary', '')
        if website_summary:
            content_sources.append(website_summary)

        # Add LinkedIn data
        linkedin_headline = lead_data.get('linkedin_headline', '')
        if linkedin_headline:
            content_sources.append(linkedin_headline)

        # Add AI analysis
        ai_value_prop = lead_data.get('ai_value_proposition', '')
        if ai_value_prop:
            content_sources.append(ai_value_prop)

        # Combine all content
        combined_content = ' '.join(content_sources).lower()

        if not combined_content:
            return hooks

        # Extract specific projects/clients (look for brand names, "for X", "with Y")
        project_patterns = [
            r'(?:for|with|client|brand|campaign)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
            r'(?:worked on|launched|created|built)\s+([a-z]+\s+[a-z]+)',
        ]
        for pattern in project_patterns:
            matches = re.findall(pattern, combined_content, re.IGNORECASE)
            hooks['specific_projects'].extend([m.strip() for m in matches if len(m) > 3])

        # Extract recent news (launches, expansions, new products)
        news_keywords = ['launched', 'expanded', 'announced', 'introduced', 'opened', 'released', 'unveiled']
        for keyword in news_keywords:
            if keyword in combined_content:
                # Extract context around the keyword
                idx = combined_content.find(keyword)
                if idx != -1:
                    context = combined_content[max(0, idx-50):min(len(combined_content), idx+100)]
                    hooks['recent_news'].append(f"{keyword}: {context.strip()}")

        # Extract tech stack
        tech_keywords = ['wordpress', 'shopify', 'react', 'python', 'javascript', 'aws', 'google analytics',
                        'mailchimp', 'hubspot', 'salesforce', 'stripe', 'zapier', 'api']
        for tech in tech_keywords:
            if tech in combined_content:
                hooks['tech_stack'].append(tech)

        # Extract achievements (awards, metrics, years)
        achievement_patterns = [
            r'(\d+\+?\s+(?:years?|clients?|customers?|projects?|awards?|employees?))',
            r'(?:award|winner|recognized|certified|accredited)',
            r'(?:grew|increased|achieved)\s+\d+%?',
        ]
        for pattern in achievement_patterns:
            matches = re.findall(pattern, combined_content, re.IGNORECASE)
            if matches:
                hooks['achievements'].extend([str(m) for m in matches])

        # Extract team info
        team_patterns = [
            r'(?:hiring|looking for|seeking)\s+([a-z\s]+)',
            r'(?:team of|staff of)\s+(\d+)',
            r'(?:joined|new)\s+([a-z]+\s+(?:director|manager|lead|officer))',
        ]
        for pattern in team_patterns:
            matches = re.findall(pattern, combined_content, re.IGNORECASE)
            if matches:
                hooks['team_info'].extend([str(m).strip() for m in matches])

        # Deduplicate and limit
        for key in hooks:
            hooks[key] = list(set(hooks[key]))[:5]  # Max 5 items per category

        return hooks

    def generate_complete_sequence(
        self,
        lead_data: Dict,
        sender_info: Dict,
        product_info: Dict
    ) -> Dict[str, Dict]:
        """
        Generate complete 5-email sequence based on lead data

        Args:
            lead_data: Complete enriched lead data {
                'name': str,
                'company': str,
                'title': str,
                'linkedin_headline': str,
                'linkedin_company': str,
                'linkedin_experience': str,
                'recent_activity': str,
                'pain_points': str,
                'industry': str,
                'trigger_events': str,
                'social_proof': str,
                'lead_score': int,
                'ai_category': str,
                'ai_value_proposition': str
            }
            sender_info: Your info {
                'name': str,
                'company': str,
                'title': str,
                'value_proposition': str
            }
            product_info: Product/service info {
                'name': str,
                'category': str,
                'key_benefit': str,
                'target_industries': List[str]
            }

        Returns:
            Dict with email_1 through email_5, each containing:
            {
                'subject': str,
                'body': str,
                'timing': str,
                'goal': str,
                'ps': str (optional)
            }
        """
        if not self.client:
            logger.error("No AI client available - API key not set")
            return self._generate_fallback_sequence(lead_data, sender_info, product_info)

        logger.info(f"Generating AI-powered email sequence for {lead_data.get('name', 'Unknown')}")

        # Extract personalization hooks from scraped content
        personalization_hooks = self.extract_personalization_hooks(lead_data)
        lead_data['personalization_hooks'] = personalization_hooks

        sequence = {}

        # Generate each email in the sequence
        for email_num in range(1, 6):
            email_key = f'email_{email_num}'
            email_config = self.sequence_structure[email_key]

            try:
                email_content = self._generate_single_email(
                    email_num=email_num,
                    email_config=email_config,
                    lead_data=lead_data,
                    sender_info=sender_info,
                    product_info=product_info
                )

                sequence[email_key] = email_content
                logger.info(f"✅ Generated {email_config['name']}")

            except Exception as e:
                logger.error(f"Failed to generate {email_key}: {e}")
                sequence[email_key] = self._generate_fallback_email(
                    email_num, email_config, lead_data, sender_info
                )

        return sequence

    def _generate_single_email(
        self,
        email_num: int,
        email_config: Dict,
        lead_data: Dict,
        sender_info: Dict,
        product_info: Dict
    ) -> Dict:
        """Generate a single email using OpenAI GPT"""

        # Build comprehensive prompt with all available data
        prompt = self._build_email_prompt(
            email_num, email_config, lead_data, sender_info, product_info
        )

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse response
        email_text = response.choices[0].message.content

        # Extract subject and body
        subject, body, ps = self._parse_email_response(email_text)

        return {
            'subject': subject,
            'body': body,
            'ps': ps,
            'timing': email_config['timing'],
            'goal': email_config['goal'],
            'name': email_config['name']
        }

    def _build_email_prompt(
        self,
        email_num: int,
        email_config: Dict,
        lead_data: Dict,
        sender_info: Dict,
        product_info: Dict
    ) -> str:
        """Build comprehensive prompt for email generation"""

        # Extract lead details
        first_name = lead_data.get('name', '').split()[0] if lead_data.get('name') else 'there'
        company = lead_data.get('company', 'the company')
        title = lead_data.get('title', '')
        industry = lead_data.get('industry', '')

        # LinkedIn data
        linkedin_headline = lead_data.get('linkedin_headline', '')
        linkedin_company = lead_data.get('linkedin_company', '')
        linkedin_experience = lead_data.get('linkedin_experience', '')

        # Enrichment data
        recent_activity = lead_data.get('recent_activity', '')
        pain_points = lead_data.get('pain_points', '')
        trigger_events = lead_data.get('trigger_events', '')
        social_proof = lead_data.get('social_proof', '')

        # AI insights
        ai_category = lead_data.get('ai_category', '')
        ai_value_prop = lead_data.get('ai_value_proposition', '')

        # Lead scoring
        lead_score = lead_data.get('lead_score', 0)

        prompt = f"""You are an expert cold email copywriter. Write Email #{email_num} of a 5-email sequence.

**EMAIL GOAL:** {email_config['goal']}
**TONE:** {email_config['tone']}
**TIMING:** {email_config['timing']} (this is email {email_num} of 5)

**LEAD INFORMATION:**
- Name: {lead_data.get('name', 'Unknown')}
- Title: {title}
- Company: {company}
- Industry: {industry}
- Lead Score: {lead_score}/100

**LINKEDIN PROFILE DATA:**
- Headline: {linkedin_headline}
- Current Company: {linkedin_company}
- Experience Summary: {linkedin_experience[:200] if linkedin_experience else 'N/A'}

**ENRICHMENT & SIGNALS:**
- Recent Activity: {recent_activity if recent_activity else 'None detected'}
- Pain Points (AI-detected): {pain_points if pain_points else 'None detected'}
- Trigger Events: {trigger_events if trigger_events else 'None detected'}
- Social Proof: {social_proof if social_proof else 'None detected'}

**AI ANALYSIS:**
- Business Category: {ai_category}
- Value Proposition: {ai_value_prop}
"""

        # Add personalization hooks if available
        hooks = lead_data.get('personalization_hooks', {})
        if hooks and any(hooks.values()):
            prompt += "\n**🎯 SPECIFIC PERSONALIZATION HOOKS (USE THESE!):**\n"

            if hooks.get('specific_projects'):
                prompt += f"- Projects/Clients Mentioned: {', '.join(hooks['specific_projects'][:3])}\n"

            if hooks.get('recent_news'):
                prompt += f"- Recent Company News: {'; '.join([n[:80] for n in hooks['recent_news'][:2]])}\n"

            if hooks.get('tech_stack'):
                prompt += f"- Tech Stack: {', '.join(hooks['tech_stack'][:5])}\n"

            if hooks.get('achievements'):
                prompt += f"- Notable Achievements: {', '.join(hooks['achievements'][:3])}\n"

            if hooks.get('team_info'):
                prompt += f"- Team Information: {', '.join(hooks['team_info'][:2])}\n"

            prompt += "\n"

        prompt += f"""
**YOUR INFO:**
- Your Name: {sender_info.get('name', 'Your Name')}
- Your Company: {sender_info.get('company', 'Your Company')}
- Your Title: {sender_info.get('title', 'Your Title')}
- Your Value Prop: {sender_info.get('value_proposition', 'We help companies grow')}

**PRODUCT/SERVICE:**
- Product: {product_info.get('name', 'Our solution')}
- Category: {product_info.get('category', 'software')}
- Key Benefit: {product_info.get('key_benefit', 'efficiency and growth')}

**INSTRUCTIONS:**
1. Use the prospect's first name: {first_name}
2. **CRITICAL: Reference SPECIFIC details from the personalization hooks above (projects, news, tech, achievements)**
3. **DO NOT use generic statements like "I've been following your work" - be specific about WHAT you saw**
4. If recent activity exists, mention it naturally with concrete details
5. If pain points detected, address them subtly
6. Keep subject line under 60 characters, make it specific to their situation
7. Keep email body 100-150 words (short and punchy)
8. Match the tone: {email_config['tone']}
9. Include ONE clear call-to-action
10. Add a relevant P.S. with a specific detail if appropriate for this email type

**EMAIL SEQUENCE CONTEXT:**
"""

        # Add context about previous/next emails
        if email_num == 1:
            prompt += "- This is the FIRST email - introduce yourself, establish relevance, create curiosity\n"
        elif email_num == 2:
            prompt += "- This is a FOLLOW-UP - provide value (insight/tip/resource) without asking for anything\n"
        elif email_num == 3:
            prompt += "- This is the SOCIAL PROOF email - share a relevant case study or data point\n"
        elif email_num == 4:
            prompt += "- This is the DIRECT ASK - clear CTA for 15-min call, respectful but confident\n"
        elif email_num == 5:
            prompt += "- This is the BREAK-UP email - humble, understanding, give them an out while keeping door open\n"

        prompt += """
**OUTPUT FORMAT:**
Return the email in this exact format:

SUBJECT: [subject line here]

BODY:
[email body here]

P.S. [optional P.S. if relevant]

**IMPORTANT:**
- Be concise (100-150 words for body)
- Be specific and personal using the data provided
- Avoid generic corporate speak
- Write like a human, not a robot
- Focus on THEM, not you
- No buzzwords or jargon
"""

        return prompt

    def _parse_email_response(self, email_text: str) -> tuple:
        """Parse AI response to extract subject, body, and P.S."""

        subject = ""
        body = ""
        ps = ""

        lines = email_text.strip().split('\n')

        current_section = None
        body_lines = []

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith('SUBJECT:'):
                subject = line_stripped.replace('SUBJECT:', '').strip()
            elif line_stripped == 'BODY:':
                current_section = 'body'
            elif line_stripped.startswith('P.S.'):
                ps = line_stripped
                current_section = None
            elif current_section == 'body' and line_stripped:
                body_lines.append(line_stripped)

        body = '\n\n'.join(body_lines)

        return subject, body, ps

    def _generate_fallback_sequence(
        self,
        lead_data: Dict,
        sender_info: Dict,
        product_info: Dict
    ) -> Dict[str, Dict]:
        """Generate basic fallback sequence without AI"""

        logger.warning("Using fallback email sequence (no AI)")

        sequence = {}

        for email_num in range(1, 6):
            email_key = f'email_{email_num}'
            email_config = self.sequence_structure[email_key]

            sequence[email_key] = self._generate_fallback_email(
                email_num, email_config, lead_data, sender_info
            )

        return sequence

    def _generate_fallback_email(
        self,
        email_num: int,
        email_config: Dict,
        lead_data: Dict,
        sender_info: Dict
    ) -> Dict:
        """Generate basic template-based email"""

        first_name = lead_data.get('name', '').split()[0] if lead_data.get('name') else 'there'
        company = lead_data.get('company', 'your company')

        # Simple template-based emails
        templates = {
            1: {
                'subject': f"Quick question about {company}",
                'body': f"Hi {first_name},\n\nI noticed your work at {company} and thought you might be interested in how we're helping similar companies improve efficiency.\n\nWorth a quick chat?",
                'ps': ""
            },
            2: {
                'subject': f"Resource for {company}",
                'body': f"Hi {first_name},\n\nThought this might be helpful for your team at {company} - sharing a quick guide on [topic].\n\nNo strings attached, hope it helps!",
                'ps': ""
            },
            3: {
                'subject': f"Results we've seen",
                'body': f"Hi {first_name},\n\nWanted to share how we helped a similar company to {company} achieve [result].\n\nThought it might be relevant for your team.",
                'ps': ""
            },
            4: {
                'subject': f"15 minutes to discuss?",
                'body': f"Hi {first_name},\n\nWould love to discuss how we could help {company} achieve similar results.\n\nOpen to a quick 15-minute call this week?",
                'ps': ""
            },
            5: {
                'subject': f"Should I close your file?",
                'body': f"Hi {first_name},\n\nHaven't heard back, so I'll assume this isn't a priority right now.\n\nFeel free to reach out if timing changes. All the best with {company}!",
                'ps': ""
            }
        }

        template = templates.get(email_num, templates[1])

        return {
            'subject': template['subject'],
            'body': template['body'],
            'ps': template['ps'],
            'timing': email_config['timing'],
            'goal': email_config['goal'],
            'name': email_config['name']
        }

    def format_sequence_for_sheets(self, sequence: Dict[str, Dict]) -> Dict[str, str]:
        """
        Format email sequence for Google Sheets columns

        Returns dict with column names as keys
        """
        formatted = {}

        for email_num in range(1, 6):
            email_key = f'email_{email_num}'
            email = sequence.get(email_key, {})

            # Create columns for each email
            formatted[f'Email {email_num} - Subject'] = email.get('subject', '')
            formatted[f'Email {email_num} - Body'] = email.get('body', '')
            formatted[f'Email {email_num} - Timing'] = email.get('timing', '')

            # Optional P.S.
            if email.get('ps'):
                formatted[f'Email {email_num} - P.S.'] = email.get('ps', '')

        # Add metadata
        formatted['Sequence Status'] = 'Generated'
        formatted['Sequence Generated At'] = datetime.now().isoformat()

        return formatted


def main():
    """Test the email sequence generator"""

    # Test data
    lead_data = {
        'name': 'Lorenzo Smith',
        'company': 'Ahead Creative',
        'title': 'Creative Director',
        'industry': 'Marketing Agency',
        'linkedin_headline': 'Creative Director helping brands tell better stories',
        'linkedin_company': 'Ahead Creative',
        'linkedin_experience': 'Leading creative strategy for 50+ brands',
        'recent_activity': 'Recently expanded into TV spot production',
        'pain_points': 'Manual client reporting | Time-consuming approval workflows | Limited analytics',
        'trigger_events': 'hiring: Hiring two new creative directors',
        'social_proof': '8 years in business | 200+ clients',
        'lead_score': 85,
        'ai_category': 'Full-service marketing agency',
        'ai_value_proposition': 'Comprehensive creative and strategic services'
    }

    sender_info = {
        'name': 'Alex Johnson',
        'company': 'WorkflowPro',
        'title': 'Head of Partnerships',
        'value_proposition': 'We help creative agencies automate client reporting and save 10+ hours/week'
    }

    product_info = {
        'name': 'WorkflowPro',
        'category': 'workflow automation',
        'key_benefit': 'automated client reporting and approval workflows',
        'target_industries': ['Marketing', 'Advertising', 'Creative Agency']
    }

    # Generate sequence
    generator = AIEmailSequenceGenerator()
    sequence = generator.generate_complete_sequence(lead_data, sender_info, product_info)

    # Display results
    print("\n" + "="*80)
    print("AI-POWERED EMAIL SEQUENCE")
    print("="*80)

    for email_num in range(1, 6):
        email_key = f'email_{email_num}'
        email = sequence.get(email_key, {})

        print(f"\n{'='*80}")
        print(f"EMAIL #{email_num}: {email.get('name', 'Unknown')}")
        print(f"Timing: {email.get('timing', 'N/A')}")
        print(f"Goal: {email.get('goal', 'N/A')}")
        print(f"{'='*80}")
        print(f"\nSUBJECT: {email.get('subject', 'N/A')}")
        print(f"\nBODY:\n{email.get('body', 'N/A')}")
        if email.get('ps'):
            print(f"\n{email.get('ps', '')}")
        print()

    # Show sheet format
    print("\n" + "="*80)
    print("GOOGLE SHEETS FORMAT")
    print("="*80)
    formatted = generator.format_sequence_for_sheets(sequence)
    for col_name, value in formatted.items():
        print(f"{col_name}: {value[:100]}..." if len(str(value)) > 100 else f"{col_name}: {value}")


if __name__ == "__main__":
    main()
