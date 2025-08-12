import asyncio
import threading
import json
import time
import cohere
import config
import os
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.console import Console

from tool_definations import get_tool_definitions, system_get_current_directory
from knowledge_graph import KnowledgeGraph

from market_research import MarketResearchAPI
from design_api import DesignAPI, show_image
from amazon_api import AmazonAPI
from facebook_api import FacebookAPI
from instagram_api import InstagramAPI
from website_manager import WebsiteManager
from whatsapp_api import WhatsAppAPI

from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from elevenlabs.client import ElevenLabs
from elevenlabs import play


class KalaSahayakAgent:
    def __init__(self, language="hi-IN"):
        self.console = Console()

        self.cohere_client = cohere.Client(api_key=config.COHERE_API_KEY)
        self.deepgram_client = DeepgramClient(config.DEEPGRAM_API_KEY)
        self.elevenlabs_client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)

        self.tools = get_tool_definitions()
        self.knowledge_graph = KnowledgeGraph()

        self.language = language
        self.voice_id = getattr(config, "ELEVENLABS_VOICE_ID", None)
        self.is_speaking = False
        self.stop_playback_event = threading.Event()
        self.task_queue = asyncio.Queue()
        self.chat_history = []

        self.preamble = """
<Persona>
🤝 You are 'Kala-Sahayak' (कला-सहायक), a multilingual elite AI assistant dedicated to empowering Indian artisans & entrepreneurs 🌸. 
You are professional 🎯, empathetic ❤️, creative 🎨, and strategically skilled in:
• Digital Marketing 📢
• E-Commerce 📦
• Creative Design 🖌️
• Social Media Engagement 📱
• Cultural Sensitivity 🌏

You adapt your tone & detail level to the user's expertise — from beginner to expert 🧠.
You are calm under pressure, always ensuring the user feels heard and understood.
</Persona>

<Core_Rules>
1️⃣ **🗣️ First Contact & Clarification** — If the user request is vague/ambiguous/conflicting, ask specific clarifying questions before acting.  
2️⃣ **🔒 Safety & Ethics** — Always ensure no harmful, illegal, unsafe, or inappropriate content is created or published. Politely refuse if needed.  
3️⃣ **🛑 Confirmation Before Irreversible Actions** — Before making public posts, publishing products, updating websites, or sending messages, confirm with the user.  
4️⃣ **📂 File Handling Protocol** — If a task needs a file/image/audio/video and no path is given, ask for it first.  
5️⃣ **🧩 Sequential Planning** — Plan steps in logical order. Never use an artifact before creating or retrieving it.  
6️⃣ **⚡ Error Handling** — If a tool fails or gives incomplete data, try alternatives or suggest manual intervention.  
7️⃣ **🌐 Cultural Context Awareness** — Respect local traditions, languages, and market realities while giving modern solutions.  
8️⃣ **🎯 Goal Alignment** — Always check if the final output aligns with the user's business/artistic goals.  
</Core_Rules>

<Special_Abilities>
✨ Multi-step reasoning for complex goals.
✨ Translation & tone adaptation in Hindi 🇮🇳 and English 🇬🇧.
✨ Context memory to refine ongoing projects.
✨ Adaptive planning for new, unexpected situations.
✨ Handling urgent tasks with prioritization logic.
</Special_Abilities>
"""

        self._initialize_tool_map()

    def _initialize_tool_map(self):
        market_api = MarketResearchAPI()
        design_api = DesignAPI()
        amazon_api = AmazonAPI()
        facebook_api = FacebookAPI()
        instagram_api = InstagramAPI()
        website_manager = WebsiteManager()
        whatsapp_api = WhatsAppAPI()

        self.tool_map = {
            "market_search_for_products": market_api.search_web,
            "market_extract_product_details": market_api.extract_product_info,
            "market_analyze_competitors": market_api.summarize_competitor_data,
            "design_create_poster": design_api.create_poster,
            "design_update_poster": design_api.update_poster,
            "display_show_local_image": show_image,
            "system_get_current_directory": system_get_current_directory,
            "facebook_post_text": facebook_api.post_text,
            "facebook_post_image": facebook_api.post_image,
            "facebook_post_video": facebook_api.post_video,
            "facebook_create_event": facebook_api.create_event,
            "facebook_get_page_feed": facebook_api.get_page_feed,
            "amazon_create_or_update_listing": amazon_api.create_or_update_listing,
            "amazon_get_listing": amazon_api.get_listing,
            "amazon_update_price": amazon_api.update_price,
            "amazon_update_inventory": amazon_api.update_inventory,
            "amazon_get_orders": amazon_api.get_orders,
            "instagram_post_image": instagram_api.post_image,
            "instagram_post_carousel": instagram_api.post_carousel,
            "instagram_post_story": instagram_api.post_story,
            "website_generate_full_website": website_manager.generate_full_website,
            "website_add_or_update_page": website_manager.add_or_update_page,
            "website_get_file_structure": website_manager.get_file_structure,
            "website_clear_directory": website_manager.clear_directory,
            "whatsapp_send_text_message": whatsapp_api.send_text_message,
            "whatsapp_send_image": whatsapp_api.send_image,
            "whatsapp_send_document": whatsapp_api.send_document,
        }

    def plan(self, user_command: str):
        message = user_command
        cached_plan = self.knowledge_graph.find_successful_plan(user_command)

        if cached_plan:
            self.console.print(
                Panel(
                    "[bold green]🧠 Found a similar plan. Revising it for current needs...[/bold green]",
                    title="Knowledge Graph Hit",
                    border_style="green",
                )
            )
            message = f"""
📌 **User’s New Request:**  
"{user_command}"

📜 **Previously Successful Plan:**  
{json.dumps(cached_plan, indent=2)}

🧠 **Your Task:**  
1️⃣ Compare the old plan with the new request.  
2️⃣ If still relevant ✅, adapt it to the new situation.  
3️⃣ If partially relevant 🔄, modify steps to fit.  
4️⃣ If irrelevant ❌, create a completely new step-by-step plan.  
5️⃣ Ensure every step follows <Core_Rules> from the preamble.  
6️⃣ Anticipate possible tool errors & add backup options.  
7️⃣ Keep output structured as a **list of tool calls** or a **direct spoken reply**.
"""

        try:
            response = self.cohere_client.chat(
                message=message,
                chat_history=self.chat_history,
                tools=self.tools,
                model="command-r-plus",
                preamble=self.preamble,
            )
            if getattr(response, "tool_calls", None):
                return [
                    {"tool_name": call.name, "parameters": call.parameters}
                    for call in response.tool_calls
                ]
            elif getattr(response, "text", None):
                return [
                    {"tool_name": "speak_direct", "parameters": {"text": response.text}}
                ]
            return []
        except Exception as e:
            self.console.print(f"[bold red]Error during planning: {e}[/bold red]")
            return [
                {
                    "tool_name": "speak_direct",
                    "parameters": {"text": "I have some connection issues. Please try again."},
                }
            ]

    def execute_tool(self, tool_name: str, parameters: dict):
        if tool_name not in self.tool_map:
            return f"Error: Tool '{tool_name}' not found."
        try:
            return self.tool_map[tool_name](**parameters)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"

    def speak(self, text: str):
        self.is_speaking = True
        self.stop_playback_event.clear()

        def play_audio():
            try:
                audio_stream = self.elevenlabs_client.generate(
                    text=text, voice=self.voice_id, model="eleven_multilingual_v2", stream=True
                )
                play(audio_stream, interrupt_event=self.stop_playback_event)
            except TypeError:
                # fallback if play doesn't accept interrupt_event in some versions
                play(audio_stream)
            except Exception as e:
                self.console.print(f"[bold red]TTS error:[/bold red] {e}")

        playback_thread = threading.Thread(target=play_audio, daemon=True)
        playback_thread.start()

        while playback_thread.is_alive():
            if self.stop_playback_event.is_set():
                break
            time.sleep(0.1)
        self.is_speaking = False

    def interrupt_speech(self):
        if self.is_speaking:
            self.console.print("[yellow]🔉 Speech interrupted by user.[/yellow]")
            self.stop_playback_event.set()

    async def listen(self):
        options = LiveOptions(model="nova-2", language=self.language, smart_format=True, interim_results=True)
        try:
            dg_connection = self.deepgram_client.listen.asynclive.v("1")

            async def on_message(result, **kwargs):
                try:
                    sentence = result.channel.alternatives[0].transcript
                except Exception:
                    sentence = ""
                if len(sentence.strip()) > 0:
                    self.interrupt_speech()
                if getattr(result, "is_final", False) and len(sentence.strip()) > 0:
                    await self.task_queue.put(sentence)

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            await dg_connection.start(options)
        except Exception as e:
            self.console.print(f"[bold red]Deepgram connection error: {e}[/bold red]")

    async def _process_tasks(self):
        while True:
            user_command = await self.task_queue.get()
            self.console.print(Panel(user_command, title="🎤 User Command", border_style="yellow"))
            self.chat_history.append({"role": "USER", "message": user_command})

            plan = await asyncio.to_thread(self.plan, user_command)
            self.console.print(Panel(str(plan), title="🧠 AI Plan", border_style="cyan"))

            if not plan:
                await asyncio.to_thread(self.speak, text="मैं इस पर स्पष्ट नहीं हूँ। कृपया इसे फिर से कहें।")
            else:
                plan_successful = True
                for step in plan:
                    tool_name, params = step.get("tool_name"), step.get("parameters", {})
                    if tool_name == "speak_direct":
                        await asyncio.to_thread(self.speak, text=params.get("text", ""))
                        self.chat_history.append({"role": "CHATBOT", "message": params.get("text", "")})
                        continue

                    result = await asyncio.to_thread(self.execute_tool, tool_name, params)
                    self.console.print(Panel(str(result), title=f"✔️ Result: {tool_name}", border_style="green"))
                    if isinstance(result, dict) and result.get("error"):
                        plan_successful = False
                    self.chat_history.append(
                        {
                            "role": "TOOL",
                            "tool_results": [
                                {"call": {"name": tool_name, "parameters": params}, "outputs": [result]}
                            ],
                        }
                    )

                if plan_successful and len(plan) > 1 and "speak_direct" not in [p.get("tool_name") for p in plan]:
                    try:
                        self.knowledge_graph.store_successful_plan(user_command, plan)
                        self.console.print(Panel("✅ Plan stored in knowledge graph", border_style="green"))
                    except Exception as e:
                        self.console.print(f"[bold red]KG store error: {e}[/bold red]")

            self.task_queue.task_done()

    async def run(self):
        self.console.print(Panel("[bold cyan]Kala-Sahayak AI Voice Agent Initialized[/]", title="🚀 System Online"))
        await asyncio.to_thread(self.speak, text="नमस्ते! मैं कला-सहायक हूँ। मैं आपकी कैसे मदद कर सकता हूँ?")

        processing_task = asyncio.create_task(self._process_tasks())
        listening_task = asyncio.create_task(self.listen())

        try:
            await asyncio.gather(processing_task, listening_task)
        finally:
            try:
                self.knowledge_graph.close()
            except Exception:
                pass


if __name__ == "__main__":
    agent = KalaSahayakAgent()
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\n🛑 Agent shutdown initiated by user.")
