import requests
import mimetypes
from pathlib import Path
import config

class WhatsAppAPI:
    BASE_URL = "https://graph.facebook.com/v19.0"

    def _make_request(self, method, endpoint, params=None, json_data=None, files=None):
        if not getattr(config, "GRAPH_API_ACCESS_TOKEN", None):
            return {"error": "API Access Token is not configured."}

        headers = {} if files else {"Content-Type": "application/json"}
        headers["Authorization"] = f"Bearer {config.GRAPH_API_ACCESS_TOKEN}"

        try:
            response = requests.request(
                method,
                f"{self.BASE_URL}/{endpoint}",
                params=params,
                headers=headers,
                json=json_data,
                files=files,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": "API request failed",
                "details": str(e),
                "response": getattr(e.response, "text", None)
            }

    def send_text_message(self, recipient_id: str, message: str):
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": message}
        }
        return self._make_request(
            "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages", json_data=payload
        )

    def _upload_media(self, file_path: str, mime_type: str):
        path_obj = Path(file_path)
        if not path_obj.exists():
            return {"error": f"File not found: {file_path}"}

        with path_obj.open("rb") as f:
            files = {"file": (path_obj.name, f, mime_type)}
            params = {"messaging_product": "whatsapp"}
            return self._make_request(
                "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/media", params=params, files=files
            )

    def send_image(self, recipient_id: str, file_path: str, caption: str = ""):
        mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
        upload_response = self._upload_media(file_path, mime_type)

        if "id" in upload_response:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_id,
                "type": "image",
                "image": {"id": upload_response["id"], "caption": caption}
            }
            return self._make_request(
                "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages", json_data=payload
            )
        return upload_response

    def send_document(self, recipient_id: str, file_path: str, caption: str = ""):
        mime_type = mimetypes.guess_type(file_path)[0] or "application/pdf"
        upload_response = self._upload_media(file_path, mime_type)

        if "id" in upload_response:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_id,
                "type": "document",
                "document": {"id": upload_response["id"], "caption": caption}
            }
            return self._make_request(
                "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages", json_data=payload
            )
        return upload_response

    def send_video(self, recipient_id: str, file_path: str, caption: str = ""):
        mime_type = mimetypes.guess_type(file_path)[0] or "video/mp4"
        upload_response = self._upload_media(file_path, mime_type)

        if "id" in upload_response:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_id,
                "type": "video",
                "video": {"id": upload_response["id"], "caption": caption}
            }
            return self._make_request(
                "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages", json_data=payload
            )
        return upload_response

    def send_location(self, recipient_id: str, latitude: float, longitude: float, name: str = "", address: str = ""):
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "location",
            "location": {
                "latitude": str(latitude),
                "longitude": str(longitude),
                "name": name,
                "address": address
            }
        }
        return self._make_request(
            "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages", json_data=payload
        )

    def send_template(self, recipient_id: str, template_name: str, language_code: str = "en_US", components: list = None):
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or []
            }
        }
        return self._make_request(
            "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages", json_data=payload
        )

    def post_whatsapp_story(self, file_path: str, caption: str = ""):
        mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
        upload_response = self._upload_media(file_path, mime_type)

        if "id" in upload_response:
            payload = {
                "messaging_product": "whatsapp",
                "status": "story",
                "type": "image" if mime_type.startswith("image") else "video",
                "image" if mime_type.startswith("image") else "video": {
                    "id": upload_response["id"],
                    "caption": caption
                }
            }
            return self._make_request(
                "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages", json_data=payload
            )
        return upload_response

    def send_poster_to_group(self, group_id: str, file_path: str, caption: str = ""):
        mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
        upload_response = self._upload_media(file_path, mime_type)

        if "id" in upload_response:
            media_type_key = "image" if mime_type.startswith("image") else "video"
            payload = {
                "messaging_product": "whatsapp",
                "to": group_id,
                "type": media_type_key,
                media_type_key: {"id": upload_response["id"], "caption": caption}
            }
            return self._make_request(
                "POST", f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages", json_data=payload
            )

        return upload_response
