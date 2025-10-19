from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ProfileData(BaseModel):
    """Standard profile data model"""
    id: Optional[str] = None
    profilePicUrl: Optional[str] = None
    followerCount: Optional[int] = 0
    bio: Optional[str] = None
    fullName: Optional[str] = None


class PostData(BaseModel):
    """Standard post data model"""
    url: str
    imageUrl: Optional[str] = None
    videoUrl: Optional[str] = None
    likeCount: Optional[int] = 0
    commentCount: Optional[int] = 0
    viewCount: Optional[int] = 0
    caption: Optional[str] = None
    timestamp: Optional[str] = None


class ScraperResponse(BaseModel):
    """Standard response model for all scrapers"""
    username: str
    platform: str
    profile: ProfileData
    posts: List[PostData]
    scrapedAt: str
    success: bool
    error: Optional[str] = None


class BaseScraper(ABC):
    """Abstract base class for all social media scrapers"""

    def __init__(self, max_posts: int = 50, timeout: int = 30):
        self.max_posts = max_posts
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def scrape_profile(self, username: str) -> Dict[str, Any]:
        """
        Scrape user profile information

        Args:
            username: Username or profile ID

        Returns:
            Dictionary containing profile data
        """
        pass

    @abstractmethod
    async def scrape_posts(self, username: str) -> List[Dict[str, Any]]:
        """
        Scrape user's posts

        Args:
            username: Username or profile ID

        Returns:
            List of post dictionaries
        """
        pass

    async def scrape(self, username: str) -> ScraperResponse:
        """
        Main scraping method that combines profile and posts

        Args:
            username: Username or profile ID

        Returns:
            ScraperResponse object with all data
        """
        try:
            self.logger.info(f"Starting scrape for username: {username}")

            # Clean username (remove @ if present)
            username = username.strip().lstrip('@')

            # Scrape profile and posts
            profile_data = await self.scrape_profile(username)
            posts_data = await self.scrape_posts(username)

            # Create response
            response = ScraperResponse(
                username=username,
                platform=self.get_platform_name(),
                profile=ProfileData(**profile_data),
                posts=[PostData(**post) for post in posts_data[:self.max_posts]],
                scrapedAt=datetime.now(timezone.utc).isoformat(),
                success=True
            )

            self.logger.info(f"Successfully scraped {len(response.posts)} posts for {username}")
            return response

        except Exception as e:
            self.logger.error(f"Error scraping {username}: {str(e)}")
            return ScraperResponse(
                username=username,
                platform=self.get_platform_name(),
                profile=ProfileData(),
                posts=[],
                scrapedAt=datetime.now(timezone.utc).isoformat(),
                success=False,
                error=str(e)
            )

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name"""
        pass

    def _extract_username_from_url(self, url: str) -> str:
        """Extract username from profile URL"""
        # This can be overridden by specific scrapers
        return url.strip().split('/')[-1].strip()