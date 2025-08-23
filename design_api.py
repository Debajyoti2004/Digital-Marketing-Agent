import google.generativeai as genai
import config
import requests
import base64
from pathlib import Path
from PIL import Image, ImageDraw
from io import BytesIO
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os
import json
import time
import threading
import http.server
import socketserver
from pyngrok import ngrok

try:
    from shotstack_sdk.api import edit_api
    from shotstack_sdk.model.clip import Clip
    from shotstack_sdk.model.track import Track
    from shotstack_sdk.model.timeline import Timeline
    from shotstack_sdk.model.output import Output
    from shotstack_sdk.model.edit import Edit
    from shotstack_sdk.model.image_asset import ImageAsset
    from shotstack_sdk.model.title_asset import TitleAsset
    from shotstack_sdk.api_client import ApiClient
    from shotstack_sdk.configuration import Configuration
    SHOTSTACK_SDK_AVAILABLE = True
except ImportError:
    SHOTSTACK_SDK_AVAILABLE = False

genai.configure(api_key=getattr(config, "GENAI_API_KEY", None))

class DesignAPI:
    IMAGE_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

    def __init__(self, model_name="gemini-1.5-flash-latest"):
        self.text_model = genai.GenerativeModel(model_name)

    def _host_images_temporarily(self, image_paths: list, directory: str):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

        port = 8000
        httpd = socketserver.TCPServer(("", port), Handler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        
        rprint(Panel(f"[cyan]✨ Local server started temporarily on port {port}...[/cyan]", title="Temporary Hosting"))

        public_url = None
        try:
            public_url = ngrok.connect(port).public_url
            rprint(Panel(f"[green]✅ Public tunnel created:[/green] {public_url}", title="ngrok Tunnel"))
            
            urls = [f"{public_url}/{Path(p).name}" for p in image_paths]
            yield urls
        finally:
            rprint(Panel("[yellow]🔌 Shutting down temporary server and tunnel...[/yellow]", title="Cleanup"))
            if public_url:
                ngrok.disconnect(public_url)
            httpd.shutdown()
            httpd.server_close()

    def _generate_creative_prompt(self, product_name: str, description: str, call_to_action: str, target_audience: str = None, brand_colors: list = None):
        prompt = f"""
        **🚀 CREATIVE BRIEF: GENERATE VIRAL MARKETING POSTER PROMPT 🚀**
        **👑 ROLE & PERSONA:**
        Act as a globally acclaimed Creative Director and a master of visual marketing strategy. Your aesthetic is a fusion of Apple's minimalist luxury and National Geographic's emotional storytelling.
        **🎯 PRIMARY OBJECTIVE:**
        Generate a single, hyper-detailed, and artistically sophisticated prompt for a text-to-image AI (like Midjourney or DALL-E 3). This prompt will be used to create a promotional poster that is guaranteed to stop scrolling, evoke emotion, and drive engagement.
        **📦 CORE INTEL:**
        * **Product Name:** `{product_name}`
        * **Core Essence:** `{description}`
        * **Call to Action:** `{call_to_action}`
        * **Target Persona:** `{target_audience or 'Aspirational general audience with an appreciation for craftsmanship'}`
        * **Brand Colors:** `{brand_colors or 'Dynamic and context-aware'}`
        **📋 MANDATORY PROMPT DIRECTIVES (Your output MUST follow this structure):**
        1.  **Conceptualize the Core Narrative:** What is the one-sentence story of this image? It must be compelling.
        2.  **Define the Visual Aesthetics:** Specify camera type, lens, film stock, and style. Be professional and precise. *Examples: "Shot on a Leica M11 with a 50mm f/0.95 Noctilux lens," "Style of a Fuji Velvia film photograph," "Unreal Engine 5 cinematic rendering."*
        3.  **Master the Lighting:** Describe the lighting with professional terms. Is it natural or studio? What is the mood? *Examples: "dramatic chiaroscuro lighting casting long shadows," "soft, diffused golden hour light from a large window," "bold, cinematic neon backlighting with volumetric haze."*
        4.  **Integrate Typography:** Describe the call to action's appearance and placement. *Example: "The text '{call_to_action}' is elegantly kerned in a clean, minimalist sans-serif font (like Helvetica Neue Light) in the lower third, subtly embossed."*
        **⚡ GOLDEN RULES & FINAL OUTPUT DIRECTIVE:**
        - Do not use generic terms. Be specific, evocative, and bold.
        - The prompt must be a single, unbroken string of text.
        - **ABSOLUTE MANDATE:** Your final output is ONLY the prompt string. No commentary. No markdown. No apologies. Just the prompt.
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
        **🚀 CREATIVE BRIEF: REFINE & PERFECT MARKETING VISUAL PROMPT 🚀**
        **👑 ROLE & PERSONA:**
        Act as an expert AI Art Director and Prompt Engineer, specializing in translating subjective human feedback into precise, machine-actionable instructions for a generative image model.
        **🎯 PRIMARY OBJECTIVE:**
        Analyze, deconstruct, and surgically rewrite the previous AI prompt to create a new, superior version that perfectly incorporates the user's corrective feedback.
        **📦 INTEL FOR REVISION:**
        * **Product:** `{product_name}`
        * **📜 Previous AI Prompt:** `"{previous_prompt}"`
        * **💬 Owner's Corrective Feedback:** `"{user_feedback}"`
        **📋 MANDATORY EXECUTION DIRECTIVES (Your reasoning process):**
        1.  **Deconstruct Feedback:** What is the core desire behind the user's words? Is it about color, mood, composition, subject, or something else?
        2.  **Translate to Visuals (The Core Logic):** Convert the subjective feedback into concrete visual instructions.
            * *IF feedback is "make it more exciting," THEN modify the prompt to "increase color saturation, use dynamic motion blur, and a low-angle shot for a heroic feel."*
            * *IF feedback is "the background is boring," THEN modify the prompt to "change the background to a bustling night market in Mumbai with vibrant bokeh lights."*
            * *IF feedback is "the font is wrong," THEN modify the prompt to "change the text style to an elegant, handwritten script font like 'Great Vibes'."*
        3.  **Surgical Rewrite:** Intelligently modify only the necessary parts of the previous prompt. Preserve the core elements that were not criticized to maintain consistency.
        **⚡ FINAL OUTPUT DIRECTIVE:**
        Return ONLY the new, updated, single-line prompt string. It must be a direct, actionable instruction for the AI. Do not include any other text, explanation, or markdown.
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
                image_clip = ImageClip(img_path, duration=duration_per_image)
                text = text_overlays[i] if i < len(text_overlays) else ""
                
                text_clip = TextClip(txt=text, fontsize=70, color='white', font='Arial-Bold', stroke_color='black', stroke_width=2)
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

    def create_promo_video_with_api(self, image_paths: list, text_overlays: list, save_path: str, duration_per_image: int = 3):
        if not SHOTSTACK_SDK_AVAILABLE:
            err = "Shotstack SDK not installed. Please run 'pip install shotstack-sdk'."
            rprint(Panel(f"[bold red]❌ {err}[/bold red]", title="Dependency Missing", border_style="red"))
            return {"error": err}

        api_key = getattr(config, "SHOTSTACK_API_KEY", None)
        if not api_key:
            return {"error": "Shotstack API key is not configured."}

        hosting_dir = os.path.dirname(os.path.abspath(image_paths[0]))
        
        for public_urls in self._host_images_temporarily(image_paths, directory=hosting_dir):
            try:
                rprint(Panel(f"[cyan]🎬 Creating promo video via Shotstack API...[/cyan]", title="Cloud Video Generation", border_style="cyan"))
                
                configuration = Configuration(host="https://api.shotstack.io/stage", api_key={'DeveloperKey': api_key})
                
                with ApiClient(configuration) as api_client:
                    api_instance = edit_api.EditApi(api_client)
                    clips = []
                    start_time = 0
                    for i, url in enumerate(public_urls):
                        image_asset = ImageAsset(src=url)
                        image_clip = Clip(asset=image_asset, start=float(start_time), length=float(duration_per_image))
                        clips.append(image_clip)
                        
                        text = text_overlays[i] if i < len(text_overlays) else ""
                        if text:
                            title_asset = TitleAsset(text=text, style="minimal", color="#ffffff", background="#000000AA")
                            title_clip = Clip(asset=title_asset, start=float(start_time), length=float(duration_per_image))
                            clips.append(title_clip)
                        start_time += duration_per_image

                    track = Track(clips=clips)
                    timeline = Timeline(tracks=[track])
                    output = Output(format="mp4", resolution="hd")
                    edit = Edit(timeline=timeline, output=output)

                    api_response = api_instance.post_render(edit)
                    render_id = api_response['response']['id']
                    
                    rprint(Panel(f"Request sent. Render ID: {render_id}. Waiting for completion...", border_style="yellow"))
                    while True:
                        status_response = api_instance.get_render(render_id)
                        status = status_response['response']['status']
                        if status == "done":
                            video_url = status_response['response']['url']
                            break
                        elif status == "failed":
                            return {"error": "Shotstack video render failed."}
                        time.sleep(5)

                    video_data = requests.get(video_url).content
                    Path(save_path).write_bytes(video_data)
                    
                    rprint(Panel(f"[bold green]✅ Cloud-rendered video saved to '{save_path}'[/bold green]", title="Success", border_style="green"))
                    return {"status": "success", "file_path": save_path}

            except Exception as e:
                err = f"Failed to create video via API: {e}"
                rprint(Panel(f"[bold red]❌ {err}[/bold red]", title="Video API Error", border_style="red"))
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

if __name__ == '__main__':
    console = Console()
    console.print(Panel("🚀 [bold green]Starting DesignAPI Full Test Suite[/bold green] 🚀", expand=False))
    
    design_tool = DesignAPI()
    output_dir = "design_test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    dummy_product_photo_path = os.path.join(output_dir, "dummy_product.png")
    img = Image.new('RGB', (500, 500), color = 'blue')
    d = ImageDraw.Draw(img)
    d.text((150,225), "Original Product", fill=(255,255,0))
    img.save(dummy_product_photo_path)
    
    poster_path = os.path.join(output_dir, "test_poster_v1.png")
    poster_v2_path = os.path.join(output_dir, "test_poster_v2.png")
    enhanced_photo_path = os.path.join(output_dir, "enhanced_product.png")
    video_path = os.path.join(output_dir, "promo_video.mp4")
    video_api_path = os.path.join(output_dir, "promo_video_from_api.mp4")

    console.rule("\n[bold]Step 1: Create Poster[/bold]")
    poster_result = design_tool.create_poster(
        product_name="Artisan Clay Pot",
        description="A hand-thrown terracotta pot, perfect for plants.",
        call_to_action="Shop the Spring Collection",
        save_path=poster_path
    )
    console.print(json.dumps(poster_result, indent=2))
    
    console.rule("\n[bold]Step 2: Update Poster[/bold]")
    prompt_for_update = poster_result.get("prompt_used")
    if prompt_for_update:
        update_result = design_tool.update_poster(
            product_name="Artisan Clay Pot",
            prompt_used=prompt_for_update,
            user_feedback="Make the background look more like a sunny garden.",
            new_save_path=poster_v2_path
        )
        console.print(json.dumps(update_result, indent=2))
    else:
        console.print("[yellow]Skipping update test as initial poster creation failed.[/yellow]")

    console.rule("\n[bold]Step 3: Enhance Product Photo[/bold]")
    enhance_result = design_tool.enhance_product_photo(
        input_path=dummy_product_photo_path,
        save_path=enhanced_photo_path
    )
    console.print(json.dumps(enhance_result, indent=2))
    
    console.rule("\n[bold]Step 4: Create Promo Video (Locally)[/bold]")
    image_assets_for_video = []
    if poster_result.get("status") == "success":
        image_assets_for_video.append(poster_result["file_path"])
    if enhance_result.get("status") == "success":
        image_assets_for_video.append(enhance_result["file_path"])

    if len(image_assets_for_video) >= 2:
        video_result = design_tool.create_promo_video(
            image_paths=image_assets_for_video,
            text_overlays=["New Arrivals!", "Professionally Enhanced"],
            save_path=video_path
        )
        console.print(json.dumps(video_result, indent=2))
    else:
        console.print("[yellow]Skipping local video creation as not enough image assets were successfully created.[/yellow]")
        
    console.rule("\n[bold]Step 5: Create Promo Video (Cloud API)[/bold]")
    if len(image_assets_for_video) >= 2:
        video_api_result = design_tool.create_promo_video_with_api(
            image_paths=image_assets_for_video,
            text_overlays=["Now Available!", "Shop Online"],
            save_path=video_api_path
        )
        console.print(json.dumps(video_api_result, indent=2))
    else:
        console.print("[yellow]Skipping cloud video creation as not enough image assets were successfully created.[/yellow]")
    
    console.rule("\n[bold]Step 6: Show Final Poster[/bold]")
    if poster_v2_path and os.path.exists(poster_v2_path):
        console.print(f"Attempting to display the final updated poster: {poster_v2_path}")
        show_result = design_tool.show_image(poster_v2_path)
        console.print(json.dumps(show_result, indent=2))
    else:
        console.print("[yellow]Skipping show image test because the final poster was not created.[/yellow]")

    console.print(Panel("🏁 [bold green]DesignAPI Test Suite Finished[/bold green] 🏁", title="Final Summary"))