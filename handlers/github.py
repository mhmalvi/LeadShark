"""
GitHub handler for repository and organization analysis.

Uses GitHub API to get repository information, organization details,
and project activity while respecting rate limits.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import requests

from .base import BaseHandler
from utils.logging import get_logger

logger = get_logger(__name__)


class GitHubHandler(BaseHandler):
    """Handler for GitHub URLs."""

    def __init__(self, config: Dict[str, Any], cache_manager=None):
        """Initialize GitHub handler.

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        super().__init__(config, cache_manager)
        self.github_token = config.get('GITHUB_TOKEN', '')  # Optional token for higher limits
        self.base_url = "https://api.github.com"

    @property
    def handler_name(self) -> str:
        """Return handler name."""
        return "github"

    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the URL.

        Args:
            url: URL to check

        Returns:
            True for GitHub URLs
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain in ['github.com', 'www.github.com']
        except Exception:
            return False

    async def process(self, url: str) -> Dict[str, Any]:
        """Process GitHub URL.

        Args:
            url: GitHub URL to process

        Returns:
            Dictionary with repository/organization information
        """
        # Check cache first
        cached = await self.get_cached_result(url)
        if cached:
            logger.debug(f"Using cached result for {url}")
            return cached

        try:
            # Parse GitHub URL
            github_info = self._parse_github_url(url)
            if not github_info:
                result = self.create_error_result(url, "Could not parse GitHub URL")
                await self.cache_result(url, result)
                return result

            # Process based on type
            if github_info['type'] == 'user':
                processed_data = await self._process_user(url, github_info['user'])
            elif github_info['type'] == 'org':
                processed_data = await self._process_organization(url, github_info['org'])
            elif github_info['type'] == 'repo':
                processed_data = await self._process_repository(url, github_info['owner'], github_info['repo'])
            else:
                processed_data = self.create_error_result(url, "Unsupported GitHub URL type")

            # Cache and return
            await self.cache_result(url, processed_data)
            return processed_data

        except Exception as e:
            logger.error(f"Error processing GitHub URL {url}: {e}")
            result = self.create_error_result(url, str(e))
            await self.cache_result(url, result)
            return result

    def _parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub URL to extract information.

        Args:
            url: GitHub URL

        Returns:
            Dictionary with URL components or None if not parseable
        """
        # Repository pattern: github.com/owner/repo
        repo_match = re.search(r'github\.com/([^/]+)/([^/\?#]+)', url)
        if repo_match:
            owner, repo = repo_match.groups()
            # Skip special GitHub paths
            if owner.lower() in ['features', 'pricing', 'explore', 'search', 'trending']:
                return None
            return {
                'type': 'repo',
                'owner': owner,
                'repo': repo
            }

        # User/organization pattern: github.com/username
        user_match = re.search(r'github\.com/([^/\?#]+)/?$', url)
        if user_match:
            user = user_match.group(1)
            if user.lower() not in ['features', 'pricing', 'explore', 'search', 'trending']:
                return {
                    'type': 'user',  # Will determine if org or user via API
                    'user': user
                }

        return None

    async def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional authentication.

        Returns:
            Headers dictionary
        """
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/vnd.github.v3+json'
        }

        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        return headers

    async def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make API request to GitHub.

        Args:
            endpoint: API endpoint (without base URL)

        Returns:
            Response data or None if failed
        """
        try:
            headers = await self._get_headers()
            url = f"{self.base_url}/{endpoint.lstrip('/')}"

            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout_seconds
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None  # Not found
            else:
                logger.warning(f"GitHub API error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error making GitHub request to {endpoint}: {e}")
            return None

    async def _process_user(self, url: str, username: str) -> Dict[str, Any]:
        """Process GitHub user profile.

        Args:
            url: Original URL
            username: GitHub username

        Returns:
            Processed user data
        """
        # Get user data
        user_data = await self._make_request(f"users/{username}")
        if not user_data:
            return self.create_error_result(url, "User not found")

        # Check if this is an organization
        if user_data.get('type') == 'Organization':
            return await self._process_organization(url, username)

        key_points = []
        signals = []

        # Basic user info
        name = user_data.get('name') or username
        bio = user_data.get('bio', '')
        location = user_data.get('location', '')
        company = user_data.get('company', '')

        key_points.append(f"User: {name}")

        if bio:
            key_points.append(f"Bio: {self.truncate_text(bio, 100)}")

        if company:
            key_points.append(f"Company: {company}")

        if location:
            key_points.append(f"Location: {location}")

        # Stats
        public_repos = user_data.get('public_repos', 0)
        followers = user_data.get('followers', 0)
        following = user_data.get('following', 0)

        key_points.append(f"Repos: {public_repos}, Followers: {followers}")

        # User signals
        if followers > 100:
            signals.append(f"Popular developer ({followers}+ followers)")

        if public_repos > 10:
            signals.append(f"Active contributor ({public_repos}+ repos)")

        # Get recent repositories
        repos = await self._make_request(f"users/{username}/repos?sort=updated&per_page=5")
        if repos:
            repo_info = self._analyze_repositories(repos)
            if repo_info['languages']:
                signals.append(f"Languages: {', '.join(list(repo_info['languages'])[:3])}")

            if repo_info['total_stars'] > 50:
                signals.append(f"Notable projects ({repo_info['total_stars']} stars total)")

        return {
            'source': 'GitHub',
            'url': url,
            'key_points': key_points,
            'signals': signals,
            'status': 'OK',
            'error': None,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }

    async def _process_organization(self, url: str, org_name: str) -> Dict[str, Any]:
        """Process GitHub organization.

        Args:
            url: Original URL
            org_name: Organization name

        Returns:
            Processed organization data
        """
        # Get organization data
        org_data = await self._make_request(f"orgs/{org_name}")
        if not org_data:
            return self.create_error_result(url, "Organization not found")

        key_points = []
        signals = []

        # Basic org info
        name = org_data.get('name') or org_name
        description = org_data.get('description', '')
        location = org_data.get('location', '')
        blog = org_data.get('blog', '')

        key_points.append(f"Organization: {name}")

        if description:
            key_points.append(f"About: {self.truncate_text(description, 120)}")

        if location:
            key_points.append(f"Location: {location}")

        if blog:
            key_points.append(f"Website: {blog}")

        # Stats
        public_repos = org_data.get('public_repos', 0)
        followers = org_data.get('followers', 0)

        key_points.append(f"Public repos: {public_repos}")

        if followers > 0:
            key_points.append(f"Followers: {followers}")

        # Organization signals
        if public_repos > 20:
            signals.append(f"Large organization ({public_repos}+ repos)")
        elif public_repos > 5:
            signals.append(f"Active organization ({public_repos}+ repos)")

        if followers > 100:
            signals.append(f"Popular organization ({followers}+ followers)")

        # Get recent repositories
        repos = await self._make_request(f"orgs/{org_name}/repos?sort=updated&per_page=10")
        if repos:
            repo_info = self._analyze_repositories(repos)
            if repo_info['languages']:
                signals.append(f"Tech stack: {', '.join(list(repo_info['languages'])[:4])}")

            if repo_info['total_stars'] > 100:
                signals.append(f"Notable projects ({repo_info['total_stars']} stars total)")

        return {
            'source': 'GitHub',
            'url': url,
            'key_points': key_points,
            'signals': signals,
            'status': 'OK',
            'error': None,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }

    async def _process_repository(self, url: str, owner: str, repo_name: str) -> Dict[str, Any]:
        """Process GitHub repository.

        Args:
            url: Original URL
            owner: Repository owner
            repo_name: Repository name

        Returns:
            Processed repository data
        """
        # Get repository data
        repo_data = await self._make_request(f"repos/{owner}/{repo_name}")
        if not repo_data:
            return self.create_error_result(url, "Repository not found")

        key_points = []
        signals = []

        # Basic repo info
        name = repo_data.get('name', repo_name)
        description = repo_data.get('description', '')
        language = repo_data.get('language', '')

        key_points.append(f"Repository: {owner}/{name}")

        if description:
            key_points.append(f"Description: {self.truncate_text(description, 120)}")

        if language:
            key_points.append(f"Primary language: {language}")

        # Stats
        stars = repo_data.get('stargazers_count', 0)
        forks = repo_data.get('forks_count', 0)
        issues = repo_data.get('open_issues_count', 0)
        size = repo_data.get('size', 0)

        key_points.append(f"Stars: {stars}, Forks: {forks}, Issues: {issues}")

        # Repository signals
        if stars > 500:
            signals.append(f"Popular project ({stars}+ stars)")
        elif stars > 50:
            signals.append(f"Notable project ({stars}+ stars)")

        if forks > 100:
            signals.append(f"Active community ({forks}+ forks)")

        # Check activity
        updated_at = repo_data.get('updated_at')
        if updated_at:
            try:
                update_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_ago = (datetime.now(timezone.utc) - update_date).days

                if days_ago <= 30:
                    signals.append("Recently updated (within 30 days)")
                elif days_ago <= 90:
                    signals.append("Actively maintained")
            except Exception:
                pass

        # Topics/tags
        topics = repo_data.get('topics', [])
        if topics:
            key_points.append(f"Topics: {', '.join(topics[:5])}")

        return {
            'source': 'GitHub',
            'url': url,
            'key_points': key_points,
            'signals': signals,
            'status': 'OK',
            'error': None,
            'last_checked': datetime.now(timezone.utc).isoformat()
        }

    def _analyze_repositories(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a list of repositories for insights.

        Args:
            repos: List of repository data

        Returns:
            Analysis results
        """
        languages = set()
        total_stars = 0
        recent_activity = 0

        for repo in repos:
            # Language
            lang = repo.get('language')
            if lang:
                languages.add(lang)

            # Stars
            stars = repo.get('stargazers_count', 0)
            total_stars += stars

            # Recent activity (updated within 90 days)
            updated_at = repo.get('updated_at')
            if updated_at:
                try:
                    update_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    days_ago = (datetime.now(timezone.utc) - update_date).days
                    if days_ago <= 90:
                        recent_activity += 1
                except Exception:
                    pass

        return {
            'languages': languages,
            'total_stars': total_stars,
            'recent_activity': recent_activity
        }