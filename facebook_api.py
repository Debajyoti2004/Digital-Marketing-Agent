import requests
import config
import os
from datetime import datetime, timedelta

class FacebookAPI:
    BASE_URL = "https://graph.facebook.com/v19.0"

    def _make_request(self, method, endpoint, params=None, data=None, files=None):
        if not config.GRAPH_API_ACCESS_TOKEN:
            return {"error": "API Access Token is not configured."}
        default_params = {'access_token': config.GRAPH_API_ACCESS_TOKEN}
        if params:
            default_params.update(params)
        try:
            if method.upper() == 'POST' and files:
                response = requests.post(f"{self.BASE_URL}/{endpoint}", params=default_params, data=data, files=files, timeout=60)
            else:
                response = requests.request(method, f"{self.BASE_URL}/{endpoint}", params=default_params, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            try:
                return {"error": f"API request failed: {e.response.text}"}
            except:
                return {"error": f"API request failed: {str(e)}"}

    def post_text(self, content: str):
        response = self._make_request('POST', f"{config.FACEBOOK_PAGE_ID}/feed", params={'message': content})
        return f"Success: Text posted with ID: {response.get('id')}." if 'id' in response else {"error": response}

    def post_image(self, content: str, image_url: str = None, image_path: str = None, published: bool = True):
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                files = {'source': f}
                params = {'caption': content, 'published': str(published).lower()}
                response = self._make_request('POST', f"{config.FACEBOOK_PAGE_ID}/photos", params=params, files=files)
        elif image_url:
            params = {'url': image_url, 'caption': content, 'published': str(published).lower()}
            response = self._make_request('POST', f"{config.FACEBOOK_PAGE_ID}/photos", params=params)
        else:
            return {"error": "Either image_url or valid image_path must be provided."}
        return f"Success: Image post created with ID: {response.get('id')}." if 'id' in response else {"error": response}

    def post_video(self, description: str, video_url: str = None, video_path: str = None, title: str = None, published: bool = True):
        if video_path and os.path.exists(video_path):
            with open(video_path, 'rb') as f:
                files = {'source': f}
                params = {'description': description, 'published': str(published).lower()}
                if title:
                    params['title'] = title
                response = self._make_request('POST', f"{config.FACEBOOK_PAGE_ID}/videos", params=params, files=files)
        elif video_url:
            params = {'file_url': video_url, 'description': description, 'published': str(published).lower()}
            if title:
                params['title'] = title
            response = self._make_request('POST', f"{config.FACEBOOK_PAGE_ID}/videos", params=params)
        else:
            return {"error": "Either video_url or valid video_path must be provided."}
        return f"Success: Video posted with ID: {response.get('id')}." if 'id' in response else {"error": response}

    def create_event(self, name: str, start_time: str, description: str, end_time: str = None, location: str = None, privacy_type: str = "OPEN"):
        params = {'name': name, 'start_time': start_time, 'description': description, 'privacy_type': privacy_type}
        if end_time:
            params['end_time'] = end_time
        if location:
            params['place'] = location
        response = self._make_request('POST', f"{config.FACEBOOK_PAGE_ID}/events", params=params)
        return f"Success: Event '{name}' created with ID {response.get('id')}" if 'id' in response else {"error": response}

    def get_page_feed(self, limit: int = 5):
        return self._make_request('GET', f"{config.FACEBOOK_PAGE_ID}/feed", params={'limit': limit, 'fields': 'id,permalink_url'})

    def get_post_comments(self, post_id: str, since_timestamp: int):
        params = {
            'fields': 'from{name},message,created_time',
            'since': since_timestamp,
            'order': 'chronological'
        }
        return self._make_request('GET', f"{post_id}/comments", params=params)

    def get_post(self, post_id: str, fields: str = "id,message,created_time,permalink_url,attachments,shares,likes.summary(true)"):
        return self._make_request('GET', f"{post_id}", params={'fields': fields})

    def get_page_insights(self, metrics: str = "page_impressions,page_engaged_users"):
        return self._make_request('GET', f"{config.FACEBOOK_PAGE_ID}/insights", params={'metric': metrics})

    def update_post(self, post_id: str, new_message: str):
        response = self._make_request('POST', f"{post_id}", params={'message': new_message})
        return {"success": True} if 'id' not in response and 'error' not in response else ({"error": response} if 'error' in response else {"success": True})

    def delete_post(self, post_id: str):
        response = self._make_request('DELETE', f"{post_id}")
        return {"success": True} if response.get('success') else {"error": response}

    def delete_event(self, event_id: str):
        response = self._make_request('DELETE', f"{event_id}")
        return {"success": True} if response.get('success') else {"error": response}

    def get_events(self, since: str = None, until: str = None, limit: int = 10, fields: str = "id,name,start_time,end_time,place,description"):
        params = {'limit': limit, 'fields': fields}
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        return self._make_request('GET', f"{config.FACEBOOK_PAGE_ID}/events", params=params)

    def get_page_details(self, fields: str = "id,name,about,link,fan_count,followers_count"):
        return self._make_request('GET', f"{config.FACEBOOK_PAGE_ID}", params={'fields': fields})