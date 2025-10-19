import json
from datetime import datetime
from tweeterpy import TweeterPy

def get_latest_posts(username, num_posts=10):
    """
    Retrieves the latest 10 posts (tweets) for a given username without login,
    along with user profile URL, profile image, header image, and tweet details.
    Handles cases where no tweets are available. Extracts direct media URLs for photos and videos.
    Saves output as a JSON file with user_id and current date in the filename.

    Args:
        username (str): Twitter/X username (e.g., 'elonmusk')
        num_posts (int): Number of latest posts to fetch (default: 10)

    Returns:
        str: Path to the saved JSON file.
    """
    twitter = TweeterPy()

    # Get user data to retrieve user_id, profile image, and header image
    try:
        user_data = twitter.get_user_data(username)
        user_id = user_data['rest_id']
        profile_image_url = user_data.get('legacy', {}).get('profile_image_url_https', '')
        header_image_url = user_data.get('legacy', {}).get('profile_banner_url', '')
    except Exception as e:
        print(f"Error fetching user data for {username}: {e}")
        user_id = ''
        profile_image_url = ''
        header_image_url = ''
        tweets = []

    # Get latest tweets (without replies, as it doesn't require login)
    try:
        tweets_response = twitter.get_user_tweets(user_id, with_replies=False, total=num_posts, pagination=True)
        tweets_data = tweets_response.get('data', [])
    except IndexError as ie:
        print(f"IndexError fetching tweets for {username}: Likely no tweets available. {ie}")
        tweets_data = []
    except Exception as e:
        print(f"Error fetching tweets for {username}: {e}")
        tweets_data = []

    # Extract tweet features
    tweets = []
    for entry in tweets_data:
        try:
            item_content = entry['content']['itemContent']
            if 'tweet_results' in item_content:
                tweet_content = item_content['tweet_results']['result']
                if isinstance(tweet_content, dict) and 'legacy' in tweet_content:
                    legacy = tweet_content['legacy']
                    # Extract media URLs properly
                    media_list = []
                    for media in legacy.get('entities', {}).get('media', []):
                        if media.get('type') == 'photo':
                            media_url = media.get('media_url_https', '')
                            if media_url:
                                media_list.append(media_url + ':orig')  # Optional: :orig for original size
                        elif media.get('type') in ['video', 'animated_gif']:
                            variants = media.get('video_info', {}).get('variants', [])
                            if variants:
                                # Pick the variant with highest bitrate
                                best_variant = max(variants, key=lambda v: v.get('bitrate', 0))
                                media_list.append(best_variant.get('url', ''))

                    tweet_info = {
                        'tweet_id': legacy.get('id_str'),
                        'text': legacy.get('full_text'),
                        'created_at': legacy.get('created_at'),
                        'likes': legacy.get('favorite_count'),
                        'retweets': legacy.get('retweet_count'),
                        'replies': legacy.get('reply_count'),
                        'quotes': legacy.get('quote_count'),
                        'views': tweet_content.get('views', {}).get('count', 'N/A'),
                        'media_urls': media_list,
                        'url': f"https://x.com/{username}/status/{legacy.get('id_str')}"
                    }
                    tweets.append(tweet_info)
        except KeyError as ke:
            print(f"KeyError parsing tweet: {ke}. Skipping this entry.")
            continue

    # User profile URL
    profile_url = f"https://x.com/{username}"

    # Prepare JSON output
    result = {
        'user_id': user_id,
        'user_profile_url': profile_url,
        'profile_image_url': profile_url + "/photo",
        'header_image_url': header_image_url,
        'latest_tweets': tweets
    }

    # Generate filename with user_id and current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    filename = f"{user_id}_{current_date}.json" if user_id else f"{username}_{current_date}.json"

    # Save to JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"JSON saved to: {filename}")
    return filename

