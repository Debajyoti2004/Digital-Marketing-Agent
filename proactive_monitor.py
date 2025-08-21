import time
from datetime import datetime, timezone
from rich import print as rprint
from rich.panel import Panel

class ProactiveMonitor:
    def __init__(self, facebook_api_client, instagram_api_client):
        self.facebook_api = facebook_api_client
        self.instagram_api = instagram_api_client
        self.last_check_timestamp = int(time.time()) - 3600

    def check_for_new_comments(self):
        rprint(Panel(f"[cyan]📡 Proactive Monitor: Checking for new comments since {datetime.fromtimestamp(self.last_check_timestamp, tz=timezone.utc)} UTC...[/cyan]", border_style="cyan"))
        
        current_timestamp = int(time.time())
        all_new_comments = []

        fb_feed = self.facebook_api.get_page_feed(limit=5)
        if fb_feed and 'data' in fb_feed:
            for post in fb_feed['data']:
                post_id = post['id']
                comments = self.facebook_api.get_post_comments(post_id, self.last_check_timestamp)
                if comments and 'data' in comments:
                    for comment in comments['data']:
                        all_new_comments.append({
                            "platform": "Facebook",
                            "user": comment.get('from', {}).get('name', 'Unknown User'),
                            "text": comment.get('message', ''),
                            "link": post.get('permalink_url', '')
                        })

        ig_media = self.instagram_api.get_user_media(limit=5)
        if ig_media and 'data' in ig_media:
            for media in ig_media['data']:
                media_id = media['id']
                comments = self.instagram_api.get_media_comments(media_id, self.last_check_timestamp)
                if comments and 'data' in comments:
                    for comment in comments['data']:
                        all_new_comments.append({
                            "platform": "Instagram",
                            "user": comment.get('from', {}).get('username', 'Unknown User'),
                            "text": comment.get('text', ''),
                            "link": media.get('permalink', '')
                        })

        self.last_check_timestamp = current_timestamp

        if not all_new_comments:
            rprint(Panel("[bold green]✅ No new customer comments found.[/bold green]", title="Monitor Result", border_style="green"))
            return {"status": "no_new_notifications"}
        
        rprint(Panel(
            f"[bold yellow]⚠️ Found {len(all_new_comments)} New Customer Comment(s)![/bold yellow]",
            title="Monitor Alert",
            border_style="yellow"
        ))
        
        return {"status": "found_updates", "notifications": all_new_comments}