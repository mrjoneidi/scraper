import asyncio
import nest_asyncio
import json
import os
from datetime import datetime
import sys
from pathlib import Path
import os
sys.path.append(str(Path(__file__).resolve().parents[1]))
from modules.youtube import YouTubeScraper

nest_asyncio.apply()

async def main():
    scraper = YouTubeScraper(max_posts=10)
    username = "yeahmadtv"
    result = await scraper.scrape(username)

    filtered_result = {
        "username": result.username,
        "profile": {
            "id": result.profile.id,
            "profilePicUrl": result.profile.profilePicUrl,
            "followerCount": result.profile.followerCount
        },
        "posts": [
            {
                "url": post.url,
                "imageUrl": post.imageUrl,
                "likeCount": post.likeCount,
                "commentCount": post.commentCount,
                "viewCount": post.viewCount
            } for post in result.posts
        ]
    }

    # Generate filename with username and current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    filename = f"{username}_{current_date}.json"

    # Save to JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(filtered_result, f, ensure_ascii=False, indent=2)

    print(f"JSON saved to: {filename}")

    # Optional: still print the JSON for console output
    print(json.dumps(filtered_result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())