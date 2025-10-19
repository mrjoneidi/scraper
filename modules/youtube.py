from typing import Dict, List, Any
import asyncio
import yt_dlp
import re
from datetime import datetime
import json
import os
from .base import BaseScraper


class YouTubeScraper(BaseScraper):
    """YouTube scraper using yt-dlp"""

    def __init__(self, max_posts: int = 50, timeout: int = 30):
        super().__init__(max_posts, timeout)
        self.ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'extract_flat': True,
            'skip_download': True,
            'getcomments': True,
            'write_comments': True,
            'extractor_args': {
                'youtube': {
                    'lang': ['en'],
                    'player_client': ['web', 'android'],
                    'comment_sort': 'top',
                }
            },
        }

    def get_platform_name(self) -> str:
        return "youtube"

    def _get_channel_url(self, username: str) -> str:
        """Convert username to channel URL"""
        if username.startswith('http'):
            return username
        elif username.startswith('@'):
            return f"https://www.youtube.com/{username}/videos"
        elif username.startswith('UC') and len(username) == 24:
            return f"https://www.youtube.com/channel/{username}/videos"
        else:
            return f"https://www.youtube.com/@{username}/videos"

    async def scrape_profile(self, username: str) -> Dict[str, Any]:
        """Scrape YouTube channel information"""
        try:
            channel_url = self._get_channel_url(username)

            ydl_opts = self.ydl_opts.copy()

            ydl_opts['extract_flat'] = True

            loop = asyncio.get_event_loop()

            def extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(channel_url, download=False)

            info = await loop.run_in_executor(None, extract_info)

            channel_id = info.get('channel_id', None)
            channel_name = info.get('channel', username)
            subscriber_count = info.get('channel_follower_count', 0)
            profile_pic = info.get("thumbnails", [{}])[-1].get("url", "")

            return {
                "id": channel_id,
                "profilePicUrl": profile_pic,
                "followerCount": subscriber_count,
                "bio": info.get('description', '')[:500] if info.get('description') else "",
                "fullName": channel_name
            }
        except Exception as e:
            self.logger.error(f"Error scraping YouTube channel {username}: {str(e)}")
            return {
                "id": None,
                "profilePicUrl": None,
                "followerCount": 0,
                "bio": "",
                "fullName": username
            }

    async def scrape_single_video(self, video_id: str) -> Dict[str, Any]:
        """Scrape detailed information for a single video"""
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            ydl_opts = self.ydl_opts.copy()
            ydl_opts['extract_flat'] = False  # Disable for full info
            ydl_opts['getcomments'] = True
            ydl_opts['write_comments'] = True

            loop = asyncio.get_event_loop()

            def extract_video_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(video_url, download=False)

            video = await loop.run_in_executor(None, extract_video_info)

            try:
                os.makedirs('/content/logs', exist_ok=True)
                with open(f'/content/logs/video_{video_id}.json', 'w', encoding='utf-8') as f:
                    json.dump(video, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Raw data saved for video {video_id}")
            except Exception as e:
                self.logger.error(f"Error saving raw data for video {video_id}: {str(e)}")

            thumbnails = video.get('thumbnails', [])
            thumbnail_url = thumbnails[-1]['url'] if thumbnails else None

            # like_count
            like_count = video.get('like_count', 0)

            # commnet_count
            comment_count_direct = video.get('comment_count', 0)
            comments_list = video.get('comments', [])
            comment_count = comment_count_direct or len(comments_list)

            upload_date = video.get('upload_date', '')
            timestamp = datetime.strptime(upload_date, '%Y%m%d').isoformat() if upload_date and len(upload_date) == 8 else ""

            self.logger.info(f"Video {video_id}: likes={like_count}, comments={comment_count}")

            return {
                "url": video_url,
                "imageUrl": thumbnail_url,
                "videoUrl": video_url,
                "likeCount": like_count,
                "commentCount": comment_count,
                "viewCount": video.get('view_count', 0),
                "caption": video.get('title', '')[:500],
                "timestamp": timestamp
            }
        except Exception as e:
            self.logger.warning(f"Error scraping video {video_id}: {str(e)}")
            return None

    async def scrape_posts(self, username: str) -> List[Dict[str, Any]]:
        """Scrape YouTube videos"""
        try:
            channel_url = self._get_channel_url(username)

            ydl_opts = self.ydl_opts.copy()
            ydl_opts['playlistend'] = self.max_posts
            ydl_opts['extract_flat'] = True

            loop = asyncio.get_event_loop()

            def extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(channel_url, download=False)

            info = await loop.run_in_executor(None, extract_info)

            try:
                os.makedirs('/content/logs', exist_ok=True)
                with open(f'/content/logs/channel_{username}.json', 'w', encoding='utf-8') as f:
                    json.dump(info, f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.logger.error(f"Error saving channel data for {username}: {str(e)}")

            posts_data = []
            entries = info.get('entries', [])

            tasks = [self.scrape_single_video(video.get('id', '')) for video in entries[:self.max_posts]]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if result and not isinstance(result, Exception):
                    posts_data.append(result)

            return posts_data

        except Exception as e:
            self.logger.error(f"Error scraping YouTube videos for {username}: {str(e)}")
            return []