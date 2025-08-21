import requests
import config
import os

class InstagramAPI:
    BASE_URL = "https://graph.facebook.com/v19.0"
    IMGUR_UPLOAD_URL = "https://api.imgur.com/3/image"

    def _make_request(self, method, endpoint, params=None, data=None):
        if not config.GRAPH_API_ACCESS_TOKEN:
            return {"error": "API Access Token is not configured."}
        default_params = {'access_token': config.GRAPH_API_ACCESS_TOKEN}
        if params: default_params.update(params)
        try:
            r = requests.request(method, f"{self.BASE_URL}/{endpoint}", params=default_params, data=data)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _upload_to_imgur(self, image_path):
        headers = {"Authorization": f"Client-ID {config.IMGUR_CLIENT_ID}"}
        with open(image_path, "rb") as img:
            r = requests.post(self.IMGUR_UPLOAD_URL, headers=headers, files={"image": img})
        return r.json().get("data", {}).get("link")

    def _format_caption(self, caption, hashtags, user_tags):
        tags_str = " ".join(f"@{tag.lstrip('@')}" for tag in user_tags) if user_tags else ""
        hash_str = " ".join(f"#{tag.lstrip('#')}" for tag in hashtags) if hashtags else ""
        parts = [caption.strip()]
        if tags_str:
            parts.append(tags_str)
        if hash_str:
            parts.append(hash_str)
        return "\n\n".join(parts).strip()

    def _update_bio_link(self, new_link):
        return self._make_request('POST', f"{config.INSTAGRAM_USER_ID}", params={"bio_link": new_link})

    def post_image(self, caption, image_path, hashtags=[], user_tags=[], bio_link=None):
        if bio_link: self._update_bio_link(bio_link)
        url = self._upload_to_imgur(image_path) if os.path.exists(image_path) else image_path
        params = {
            'image_url': url,
            'caption': self._format_caption(caption, hashtags, user_tags)
        }
        r = self._make_request('POST', f"{config.INSTAGRAM_BUSINESS_ID}/media", params=params)
        if 'id' not in r: return r
        publish = self._make_request('POST', f"{config.INSTAGRAM_BUSINESS_ID}/media_publish", params={'creation_id': r['id']})
        return publish

    def post_carousel(self, caption, image_paths, hashtags=[], user_tags=[], bio_link=None):
        if bio_link: self._update_bio_link(bio_link)
        child_ids = []
        for path in image_paths:
            url = self._upload_to_imgur(path) if os.path.exists(path) else path
            r = self._make_request('POST', f"{config.INSTAGRAM_BUSINESS_ID}/media", params={'image_url': url, 'is_carousel_item': True})
            if 'id' in r: child_ids.append(r['id'])
        r = self._make_request('POST', f"{config.INSTAGRAM_BUSINESS_ID}/media", params={
            'caption': self._format_caption(caption, hashtags, user_tags),
            'children': ','.join(child_ids),
            'media_type': 'CAROUSEL'
        })
        if 'id' not in r: return r
        publish = self._make_request('POST', f"{config.INSTAGRAM_BUSINESS_ID}/media_publish", params={'creation_id': r['id']})
        return publish

    def post_story(self, image_path, caption="", hashtags=[], user_tags=[], link_url=None, x=0.5, y=0.8, music_track_id=None):
        url = self._upload_to_imgur(image_path) if os.path.exists(image_path) else image_path
        story_params = {
            'image_url': url,
            'caption': self._format_caption(caption, hashtags, user_tags),
            'media_type': 'STORY'
        }
        interactive = []
        if link_url:
            interactive.append({'type': 'LINK', 'link': link_url, 'x': x, 'y': y})
        if music_track_id:
            interactive.append({'type': 'MUSIC', 'music_id': music_track_id})
        if interactive:
            story_params['interactive_elements'] = interactive
        r = self._make_request('POST', f"{config.INSTAGRAM_BUSINESS_ID}/media", params=story_params)
        if 'id' not in r: return r
        publish = self._make_request('POST', f"{config.INSTAGRAM_BUSINESS_ID}/media_publish", params={'creation_id': r['id']})
        return publish

    def get_user_media(self, limit: int = 5):
        params = {'fields': 'id,permalink', 'limit': limit}
        return self._make_request('GET', f"{config.INSTAGRAM_BUSINESS_ID}/media", params=params)

    def get_media_comments(self, media_id: str, since_timestamp: int):
        params = {
            'fields': 'from{username},text,timestamp',
            'since': since_timestamp
        }
        return self._make_request('GET', f"{media_id}/comments", params=params)