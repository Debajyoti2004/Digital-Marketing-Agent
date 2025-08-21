import google.generativeai as genai
import config
import requests
import base64
from pathlib import Path
from PIL import Image
from io import BytesIO
from rich import print as rprint
from rich.panel import Panel
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips

genai.configure(api_key=getattr(config, "GENAI_API_KEY", None))

class DesignAPI:
    IMAGE_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"

    def __init__(self, model_name="gemini-pro"):
        self.text_model = genai.GenerativeModel(model_name)

    def _generate_creative_prompt(self, product_name: str, description: str, call_to_action: str, target_audience: str = None, brand_colors: list = None):
        prompt = f"""
        🎨✨ **ROLE:** World-class creative director & digital marketing expert  
        🎯 **TASK:** Generate one ultra-detailed, emotionally compelling, visually rich prompt for an AI text-to-image model to create a standout promotional poster.  
        📦 **PRODUCT DETAILS:**  
        • Name: {product_name}  
        • Description: {description}  
        • Call to Action: "{call_to_action}"  
        • Target Audience: {target_audience or 'general audience'}  
        • Brand Colors: {brand_colors or 'none specified'}  
        🖼️ **VISUAL STYLE:**  
        Describe subject, setting, mood, lighting, composition, color palette, and style (e.g., cinematic, photorealistic, vibrant, hyper-detailed).  
        Integrate the call to action text naturally into the design. Emphasize impact, clarity, and brand personality.  
        ⚡ **OUTPUT:** Return a single, rich prompt line optimized for marketing poster generation — no extra commentary.
        """
        try:
            response = self.text_model.generate_content(prompt)
            prompt_text = response.text.strip().replace("\n", " ")
            rprint(Panel(f"[bold magenta]Creative Prompt Generated[/bold magenta]\n\n{prompt_text}", title="🎨 Creative Prompt", border_style="magenta"))
            return prompt_text
        except Exception as e:
            fallback = (f"Ultra-detailed commercial product poster of '{product_name}', "
                        f"{description}, vibrant colors, dramatic lighting, clean layout, "
                        f"integrated call to action '{call_to_action}', digital marketing style.")
            rprint(Panel(f"[bold red]Fallback Prompt Used[/bold red]\n\n{fallback}", title="⚠️ Fallback Prompt", border_style="red"))
            return fallback

    def _generate_update_prompt(self, product_name: str, previous_prompt: str, user_feedback: str):
        prompt = f"""
        🔄🎨 **ROLE:** Expert AI art director & marketing creative  
        🎯 **TASK:** Refine the existing AI image prompt based on detailed user feedback for promotional marketing material.
        📦 **PRODUCT:** '{product_name}'  
        📜 **PREVIOUS PROMPT:** "{previous_prompt}"  
        💬 **USER FEEDBACK:** "{user_feedback}"
        🎯 **INSTRUCTIONS:**  
        Convert vague feedback into concrete visual changes: color shifts, lighting adjustments, style updates, composition tweaks, mood changes.  
        Ensure the updated prompt enhances emotional impact and marketing effectiveness.
        ⚡ **OUTPUT:** Return a single updated, highly descriptive prompt line optimized for AI image generation.
        """
        try:
            response = self.text_model.generate_content(prompt)
            updated_prompt = response.text.strip().replace("\n", " ")
            rprint(Panel(f"[bold cyan]Update Prompt Generated[/bold cyan]\n\n{updated_prompt}", title="🔄 Updated Prompt", border_style="cyan"))
            return updated_prompt
        except Exception as e:
            fallback = f"{previous_prompt}, updated to reflect user feedback: {user_feedback}"
            rprint(Panel(f"[bold yellow]Fallback Update Prompt Used[/bold yellow]\n\n{fallback}", title="⚠️ Fallback Update Prompt", border_style="yellow"))
            return fallback

    def _generate_image_from_prompt(self, prompt: str, save_path: str):
        api_key = getattr(config, "STABILITY_API_KEY", None)
        if not api_key:
            err = "Stability AI API key is missing."
            rprint(Panel(f"[bold red]{err}[/bold red]", title="❌ API Key Missing", border_style="red"))
            return {"error": err}
        headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        body = {"steps": 40, "width": 1024, "height": 1024, "seed": 0, "cfg_scale": 7, "samples": 1, "text_prompts": [{"text": prompt, "weight": 1}]}
        try:
            rprint(Panel(f"[bold green]Sending image generation request to Stability AI...[/bold green]", title="🚀 Generating Image", border_style="green"))
            response = requests.post(self.IMAGE_API_URL, headers=headers, json=body, timeout=90)
            response.raise_for_status()
            data = response.json()
            image_b64 = data["artifacts"][0]["base64"]
            image_data = base64.b64decode(image_b64)
            output_file = Path(save_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(image_data)
            rprint(Panel(f"[bold green]Image saved successfully:[/bold green]\n{str(output_file.resolve())}", title="✅ Success", border_style="green"))
            return {"status": "success", "file_path": str(output_file.resolve())}
        except requests.exceptions.RequestException as e:
            error_text = f"API request failed: {str(e)}"
            rprint(Panel(f"[bold red]{error_text}[/bold red]", title="❌ API Request Failed", border_style="red"))
            return {"error": error_text, "details": e.response.text if e.response else "No response"}
        except (KeyError, IndexError):
            err = "Failed to parse image from API response."
            rprint(Panel(f"[bold red]{err}[/bold red]", title="❌ Parsing Error", border_style="red"))
            return {"error": err}

    def create_poster(self, product_name: str, description: str, call_to_action: str, save_path: str, target_audience: str = None, brand_colors: list = None):
        creative_prompt = self._generate_creative_prompt(product_name, description, call_to_action, target_audience, brand_colors)
        result = self._generate_image_from_prompt(creative_prompt, save_path)
        if result.get("status") == "success":
            result["prompt_used"] = creative_prompt
        return result

    def update_poster(self, product_name: str, prompt_used: str, user_feedback: str, new_save_path: str):
        update_prompt = self._generate_update_prompt(product_name, prompt_used, user_feedback)
        result = self._generate_image_from_prompt(update_prompt, new_save_path)
        if result.get("status") == "success":
            result["prompt_used"] = update_prompt
        return result

    def enhance_product_photo(self, input_path: str, save_path: str):
        api_key = getattr(config, "REMOVE_BG_API_KEY", None)
        if not api_key:
            err = "remove.bg API key not configured."
            rprint(Panel(f"[bold red]❌ {err}[/bold red]", title="API Key Missing", border_style="red"))
            return {"error": err}

        try:
            rprint(Panel(f"[cyan]✨ Enhancing photo '{input_path}'...[/cyan]", title="Photo Enhancement", border_style="cyan"))
            with open(input_path, 'rb') as f:
                response = requests.post('https://api.remove.bg/v1.0/removebg', files={'image_file': f}, data={'size': 'auto'}, headers={'X-Api-Key': api_key})
            response.raise_for_status()

            background = Image.new('RGB', (1080, 1080), color='#F0F0F0')
            product_img = Image.open(BytesIO(response.content)).convert("RGBA")
            
            bg_w, bg_h = background.size
            img_w, img_h = product_img.size
            offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
            
            background.paste(product_img, offset, product_img)
            background.save(save_path, 'PNG')

            rprint(Panel(f"[bold green]✅ Enhanced photo saved to '{save_path}'[/bold green]", title="Success", border_style="green"))
            return {"status": "success", "file_path": save_path}
        except Exception as e:
            err = f"Failed to enhance photo: {e}"
            rprint(Panel(f"[bold red]❌ {err}[/bold red]", title="Error", border_style="red"))
            return {"error": err}

    def create_promo_video(self, image_paths: list, text_overlays: list, save_path: str, duration_per_image: int = 3):
        try:
            rprint(Panel(f"[cyan]🎬 Creating promo video, saving to '{save_path}'...[/cyan]", title="Video Generation", border_style="cyan"))
            clips = []
            for i, img_path in enumerate(image_paths):
                image_clip = ImageClip(img_path).set_duration(duration_per_image)
                text = text_overlays[i] if i < len(text_overlays) else ""
                
                text_clip = TextClip(text, fontsize=70, color='white', font='Arial-Bold', stroke_color='black', stroke_width=2)
                text_clip = text_clip.set_position('center').set_duration(duration_per_image)
                
                video_clip = CompositeVideoClip([image_clip, text_clip])
                clips.append(video_clip)
            
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(save_path, fps=24, codec="libx264", verbose=False, logger=None)

            rprint(Panel(f"[bold green]✅ Promo video saved to '{save_path}'[/bold green]", title="Success", border_style="green"))
            return {"status": "success", "file_path": save_path}
        except Exception as e:
            err = f"Failed to create video: {e}"
            rprint(Panel(f"[bold red]❌ {err}[/bold red]", title="Video Error", border_style="red"))
            return {"error": err}

    def show_image(self, file_path: str):
        try:
            path = Path(file_path)
            if not path.exists():
                err = f"File not found: {file_path}"
                rprint(Panel(f"[bold red]❌ {err}[/bold red]", title="File Error", border_style="red"))
                return {"error": err}
            
            img = Image.open(file_path)
            img.show(title=path.name)
            
            rprint(Panel(f"[bold green]🖼️ Image displayed successfully:[/bold green] {file_path}", title="Image Display", border_style="green"))
            return {"status": "success", "message": f"Displayed image '{file_path}'."}

        except Exception as e:
            err = f"Failed to display image: {e}"
            rprint(Panel(f"[bold red]❌ {err}[/bold red]", title="Display Error", border_style="red"))
            return {"error": err}