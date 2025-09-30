#!/usr/bin/env python3
"""
Link Type Classifier for Platform-Specific Field Extraction
Classifies URLs by platform and provides extraction templates
"""

import re
from urllib.parse import urlparse
from typing import Dict, List, Optional
from enum import Enum


class LinkType(Enum):
    """Enumeration of supported link types"""
    LINKEDIN_PROFILE = "linkedin_profile"
    LINKEDIN_COMPANY = "linkedin_company"
    WEBSITE = "website"
    TWITTER = "twitter"
    GITHUB = "github"
    CRUNCHBASE = "crunchbase"
    ANGELLIST = "angellist"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    BLOG_POST = "blog_post"
    JOB_POSTING = "job_posting"
    CONTACT_PAGE = "contact_page"
    GENERIC = "generic"


class LinkTypeClassifier:
    """Classifies URLs and provides platform-specific extraction templates"""

    def __init__(self):
        self.platform_patterns = {
            LinkType.LINKEDIN_PROFILE: [
                r'linkedin\.com/in/[\w-]+',
                r'linkedin\.com/pub/[\w-]+',
            ],
            LinkType.LINKEDIN_COMPANY: [
                r'linkedin\.com/company/[\w-]+',
            ],
            LinkType.TWITTER: [
                r'twitter\.com/[\w]+',
                r'x\.com/[\w]+',
            ],
            LinkType.GITHUB: [
                r'github\.com/[\w-]+',
            ],
            LinkType.CRUNCHBASE: [
                r'crunchbase\.com/organization/[\w-]+',
                r'crunchbase\.com/person/[\w-]+',
            ],
            LinkType.ANGELLIST: [
                r'angel\.co/[\w-]+',
                r'wellfound\.com/[\w-]+',
            ],
            LinkType.YOUTUBE: [
                r'youtube\.com/(@|channel/|user/)[\w-]+',
            ],
            LinkType.INSTAGRAM: [
                r'instagram\.com/[\w.]+',
            ],
            LinkType.TIKTOK: [
                r'tiktok\.com/@[\w.]+',
            ],
            LinkType.FACEBOOK: [
                r'facebook\.com/[\w.]+',
            ],
        }

        # URL path patterns for specific page types
        self.path_patterns = {
            LinkType.CONTACT_PAGE: [
                r'/contact',
                r'/get-in-touch',
                r'/reach-us',
            ],
            LinkType.JOB_POSTING: [
                r'/jobs?/',
                r'/careers?/',
                r'/hiring',
            ],
            LinkType.BLOG_POST: [
                r'/blog/',
                r'/post/',
                r'/articles?/',
            ],
        }

    def classify_url(self, url: str) -> LinkType:
        """Classify a URL into a specific link type"""
        if not url:
            return LinkType.GENERIC

        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            full_url = url.lower()

            # Check platform patterns
            for link_type, patterns in self.platform_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, full_url):
                        return link_type

            # Check path patterns for generic websites
            for link_type, patterns in self.path_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, path):
                        return link_type

            # If it's a company website (generic)
            if domain and not any(social in domain for social in [
                'linkedin', 'twitter', 'x.com', 'facebook', 'instagram',
                'github', 'youtube', 'tiktok', 'crunchbase', 'angel'
            ]):
                return LinkType.WEBSITE

            return LinkType.GENERIC

        except Exception:
            return LinkType.GENERIC

    def get_extraction_template(self, link_type: LinkType) -> Dict[str, List[str]]:
        """Get field extraction template for a link type"""
        templates = {
            LinkType.LINKEDIN_PROFILE: {
                'priority_fields': [
                    'profile_url', 'full_name', 'headline', 'current_title',
                    'company', 'location', 'summary', 'about',
                    'top_experiences', 'education', 'skills',
                    'endorsements_count', 'profile_image_url', 'contact_info'
                ],
                'selectors': {
                    'headline': ['.pv-top-card-section__headline', '.text-body-medium'],
                    'location': ['.pv-top-card-section__location', '.pb2.t-black--light'],
                    'about': ['.pv-about-section', '#about'],
                }
            },
            LinkType.LINKEDIN_COMPANY: {
                'priority_fields': [
                    'url', 'company_name', 'tagline', 'description',
                    'industry', 'company_size', 'headquarters', 'website',
                    'specialties', 'founded_year'
                ],
                'selectors': {
                    'company_name': ['.org-top-card-summary__title'],
                    'tagline': ['.org-top-card-summary__tagline'],
                    'description': ['.org-about-us-section'],
                }
            },
            LinkType.WEBSITE: {
                'priority_fields': [
                    'url', 'company_name', 'tagline', 'description',
                    'services_products', 'key_people', 'address', 'locations',
                    'email_contacts', 'phone_numbers', 'social_links',
                    'pricing_or_plans', 'tech_stack'
                ],
                'selectors': {
                    'description': ['meta[name="description"]', '.about', '#about'],
                    'email': ['a[href^="mailto:"]'],
                    'phone': ['a[href^="tel:"]'],
                }
            },
            LinkType.TWITTER: {
                'priority_fields': [
                    'url', 'handle', 'name', 'bio', 'location',
                    'followers_count', 'following_count', 'recent_tweets',
                    'engagement_indicator', 'verified'
                ],
                'selectors': {
                    'bio': ['[data-testid="UserDescription"]'],
                    'followers': ['[href$="/followers"] span'],
                }
            },
            LinkType.GITHUB: {
                'priority_fields': [
                    'url', 'username', 'display_name', 'bio',
                    'top_repos', 'followers_count', 'languages_used',
                    'organizations'
                ],
                'selectors': {
                    'bio': ['.p-note'],
                    'repos': ['[data-filterable-for="your-repos-filter"]'],
                }
            },
            LinkType.CRUNCHBASE: {
                'priority_fields': [
                    'url', 'company_name', 'description', 'founded_year',
                    'headquarters', 'funding_stage', 'total_funding',
                    'key_team', 'investors', 'latest_news'
                ],
                'selectors': {}
            },
            LinkType.YOUTUBE: {
                'priority_fields': [
                    'url', 'channel_name', 'subscribers_count',
                    'recent_video_titles', 'channel_description',
                    'engagement_sample'
                ],
                'selectors': {}
            },
            LinkType.INSTAGRAM: {
                'priority_fields': [
                    'url', 'handle', 'bio', 'followers_count',
                    'engagement_sample', 'top_hashtags'
                ],
                'selectors': {}
            },
            LinkType.CONTACT_PAGE: {
                'priority_fields': [
                    'url', 'emails_found', 'phones_found', 'contact_form'
                ],
                'selectors': {
                    'email': ['a[href^="mailto:"]', 'input[type="email"]'],
                    'phone': ['a[href^="tel:"]', 'input[type="tel"]'],
                }
            },
            LinkType.JOB_POSTING: {
                'priority_fields': [
                    'url', 'job_title', 'company', 'location',
                    'employment_type', 'posted_date',
                    'job_description_summary', 'seniority_level', 'apply_link'
                ],
                'selectors': {}
            },
            LinkType.BLOG_POST: {
                'priority_fields': [
                    'url', 'page_title', 'meta_description', 'author',
                    'publish_date', 'excerpt', 'contact_info_found'
                ],
                'selectors': {
                    'author': ['.author', '[rel="author"]', '.byline'],
                    'date': ['time', '.published', '.date'],
                }
            },
            LinkType.GENERIC: {
                'priority_fields': [
                    'url', 'page_title', 'meta_description', 'excerpt'
                ],
                'selectors': {}
            }
        }

        return templates.get(link_type, templates[LinkType.GENERIC])

    def get_json_schema(self, link_type: LinkType) -> Dict:
        """Get JSON schema for link type"""
        base_schema = {
            "source": link_type.value,
            "url": None,
            "extracted": {
                "title": None,
                "name": None,
                "company": None,
                "location": None,
                "description": None,
                "key_fields": {},
                "contacts": {
                    "emails": [],
                    "phones": []
                },
                "metrics": {
                    "followers": None,
                    "stars": None,
                    "subscribers": None
                },
                "top_items": [],
                "raw_text_snippet": None
            },
            "confidence": 0.0,
            "scrape_timestamp": None
        }

        return base_schema

    def classify_multiple_urls(self, urls: List[str]) -> Dict[str, LinkType]:
        """Classify multiple URLs"""
        return {url: self.classify_url(url) for url in urls}

    def get_display_name(self, link_type: LinkType) -> str:
        """Get human-readable name for link type"""
        display_names = {
            LinkType.LINKEDIN_PROFILE: "LinkedIn Profile",
            LinkType.LINKEDIN_COMPANY: "LinkedIn Company",
            LinkType.WEBSITE: "Company Website",
            LinkType.TWITTER: "Twitter/X",
            LinkType.GITHUB: "GitHub",
            LinkType.CRUNCHBASE: "Crunchbase",
            LinkType.ANGELLIST: "AngelList",
            LinkType.YOUTUBE: "YouTube Channel",
            LinkType.INSTAGRAM: "Instagram",
            LinkType.TIKTOK: "TikTok",
            LinkType.FACEBOOK: "Facebook",
            LinkType.BLOG_POST: "Blog Post",
            LinkType.JOB_POSTING: "Job Posting",
            LinkType.CONTACT_PAGE: "Contact Page",
            LinkType.GENERIC: "Generic Web Page"
        }
        return display_names.get(link_type, "Unknown")


# Test function
if __name__ == "__main__":
    classifier = LinkTypeClassifier()

    test_urls = [
        "https://linkedin.com/in/johndoe",
        "https://linkedin.com/company/acme-corp",
        "https://twitter.com/johndoe",
        "https://github.com/johndoe",
        "https://acmecorp.com",
        "https://acmecorp.com/contact",
        "https://acmecorp.com/blog/my-post",
        "https://youtube.com/@johndoe",
        "https://crunchbase.com/organization/acme-corp"
    ]

    print("Link Type Classification Test\n")
    for url in test_urls:
        link_type = classifier.classify_url(url)
        display_name = classifier.get_display_name(link_type)
        template = classifier.get_extraction_template(link_type)

        print(f"URL: {url}")
        print(f"  Type: {display_name}")
        print(f"  Priority Fields: {', '.join(template['priority_fields'][:5])}...")
        print()