import asyncio
import threading
import json
import time
import cohere
import config
import os
from rich.panel import Panel
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
from chroma_manager import ChromaDBManager
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from elevenlabs.client import ElevenLabs
from elevenlabs import play

class KalaSahayakAgent:
    def __init__(self, language="en-IN"):
        self.console = Console()
        self.cohere_client = cohere.Client(api_key=config.COHERE_API_KEY)
        self.deepgram_client = DeepgramClient(config.DEEPGRAM_API_KEY)
        self.elevenlabs_client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
        self.tools = get_tool_definitions()
        self.knowledge_graph = KnowledgeGraph()
        self.chroma_manager = ChromaDBManager()
        self.language = language
        self.voice_id = getattr(config, "ELEVENLABS_VOICE_ID", None)
        self.is_speaking = False
        self.stop_playback_event = threading.Event()
        self.task_queue = asyncio.Queue()
        self.welcome_messages = {
            "en-IN": "🙏 Hello! I’m Kala-Sahayak 🤖 — your creative & strategic ally. How can I help today?",
            "hi-IN": "🙏 नमस्ते! मैं कला-सहायक 🤖 — आपका रचनात्मक और रणनीतिक साथी। मैं आपकी कैसे मदद कर सकता हूँ?"
        }

        self.preamble = """
🧭 <Identity>
You are Kala-Sahayak — an advanced, multilingual, and culturally-aware AI assistant designed for Indian artisans, entrepreneurs, creators, and teams. 
You operate as a strategic partner across:
- 📢 Digital Marketing
- 🛒 E-Commerce
- 🎨 Creative Design
- 📱 Social Media
- 🎯 Product Strategy
- 🔍 Market Research
- 🛠️ Tech Troubleshooting
- 📊 Business Operations
- 🎓 Education & Training
- 🤝 Negotiation & Communication
You adapt tone, complexity, and formality to the user’s expertise level (beginner 🐣, intermediate 🚀, expert 🏆), remaining practical, ethical, and results-driven.
</Identity>

⚖️ <Guardrails>
1) 🛡️ Safety & Legality: Decline harmful, illegal, or unsafe requests.
2) 🔒 Privacy: Never reveal sensitive data or stored credentials.
3) ✅ Confirmation Before Impact: Request explicit confirmation before performing irreversible or high-impact actions.
4) 📊 Accuracy: Prefer verifiable, factual, and evidence-based responses.
5) 🤗 Cultural Sensitivity: Communicate respectfully across languages, regions, and cultures.
6) 🔄 Recovery: If a tool fails, retry with fallback options or manual guidance.

🧠 <Reasoning & Problem-Solving>
1) Clarify → Plan → Execute → Verify → Summarize → Suggest Next Steps.
2) Handle incomplete, vague, or contradictory inputs by:
   - Asking clarifying questions
   - Offering possible interpretations
   - Suggesting alternative approaches
3) For multi-step problems:
   - Break into sub-tasks
   - Execute in logical sequence
   - Validate each step before proceeding
4) For tool execution:
   - If primary tool fails, try secondary tools
   - If all fail, give actionable manual instructions
5) Use critical thinking, structured reasoning, and data-driven recommendations.

💬 <Communication & Output Style>
1) Structure responses with clear **headings**, **bullet points**, and **actionable steps**.
2) Use symbols for clarity:
   ✅ Success  
   ⚠️ Caution  
   ❌ Error  
   🔄 Retry  
   🧩 Tip  
   🗂️ Summary  
   📌 Note  
   📍 Location  
3) Balance brevity with completeness — avoid unnecessary jargon unless the user is an expert.
4) Always end with **Next Steps** or **Follow-up Questions**.

🛠️ <Special Modes>
- If user input is urgent or emergency-related, prioritize concise, action-oriented instructions.
- If input is creative (design, marketing, content), offer multiple style/format options.
- If technical error occurs, provide step-by-step manual workaround.
- If the request is outside available tools, offer realistic alternatives or external resources.

📌 <Meta-Behavior>
- Always stay in role as Kala-Sahayak.
- Keep interaction user-friendly, collaborative, and goal-focused.
- Maintain awareness of session history for better continuity.
- Clearly signal uncertainties and assumptions.
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
            "market_research_search_web": market_api.search_web,
            "market_research_analyze_product_page": market_api.analyze_product_page,
            "market_research_summarize_competitor_data": market_api.summarize_competitor_data,
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

    async def handle_command(self, user_command: str):
        self.console.print(Panel(user_command, title="💬 User Command Received", border_style="yellow", expand=False))
        self.chroma_manager.add_user_message(content=user_command, language=self.language)

        plan = await asyncio.to_thread(self.plan, user_command)
        self.console.print(Panel(json.dumps(plan, indent=2), title="🧠 AI Plan", border_style="cyan", expand=False))

        if not plan:
            return "🤔 I’m unsure how to proceed. Please rephrase or provide one objective."

        final_response_text = ""
        plan_successful = True

        for step in plan:
            tool_name = step.get("tool_name")
            params = step.get("parameters", {})

            if tool_name == "speak_direct":
                final_response_text = params.get("text", "✅ Task completed.")
                self.chroma_manager.add_chatbot_message(content=final_response_text, language=self.language)
                break

            result = await asyncio.to_thread(self.execute_tool, tool_name, params)
            self.chroma_manager.add_tool_message(call=step, outputs=[result], language=self.language)

            if isinstance(result, (dict, list)):
                display_result = Syntax(json.dumps(result, indent=2, default=str), "json", theme="monokai", line_numbers=True)
            else:
                display_result = str(result)
            self.console.print(Panel(display_result, title=f"📦 Tool Result • {tool_name}", border_style="green", expand=False))

            if isinstance(result, dict) and result.get("error"):
                plan_successful = False
                final_response_text = f"❌ Tool `{tool_name}` failed: {result.get('error')}"
                self.chroma_manager.add_chatbot_message(content=final_response_text, language=self.language)
                break

        if not final_response_text:
            try:
                chat_history = self.chroma_manager.get_formatted_history()
                summary_response = await asyncio.to_thread(
                    self.cohere_client.chat,
                    message="Summarize for the user what was accomplished. Use symbols, list key results, and next steps. Keep it concise.",
                    chat_history=chat_history,
                    model="command-r"
                )
                final_response_text = summary_response.text
                self.chroma_manager.add_chatbot_message(content=final_response_text, language=self.language)
            except Exception as e:
                self.console.print(f"[bold red]❌ Summarization Error: {e}[/bold red]")
                final_response_text = "✅ Tasks executed. 🗂️ Summary unavailable due to an error."

        if plan_successful and len(plan) > 0 and "speak_direct" not in [p.get("tool_name") for p in plan]:
            try:
                self.knowledge_graph.store_successful_plan(user_command, plan)
                self.console.print(Panel("🗂️ Plan stored in Knowledge Graph", border_style="green", expand=False))
            except Exception as e:
                self.console.print(f"[bold red]⚠️ KG Store Error: {e}[/bold red]")

        return final_response_text

    def process_text_query(self, query: str):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.handle_command(query), loop)
            return future.result()
        else:
            return loop.run_until_complete(self.handle_command(query))

    def plan(self, user_command: str):
        message = user_command
        chat_history = self.chroma_manager.get_formatted_history()
        cached_plan = self.knowledge_graph.find_successful_plan(user_command)

        if cached_plan:
            self.console.print(Panel("♻️ Similar plan found — revising…", border_style="green", expand=False))
            message = (
                f"User Request: \"{user_command}\"\n"
                f"Previous Plan: {json.dumps(cached_plan)}\n"
                f"Task: Adapt or discard this plan, then return tool calls. If no tools needed, return a speak_direct."
            )

        try:
            response = self.cohere_client.chat(
                message=message,
                chat_history=chat_history,
                tools=self.tools,
                model="command-r",
                preamble=self.preamble
            )
            return response.tool_calls or ([{"tool_name": "speak_direct", "parameters": {"text": response.text}}] if response.text else [])
        except Exception as e:
            self.console.print(f"[bold red]❌ Planning Error: {e}[/bold red]")
            return [{"tool_name": "speak_direct", "parameters": {"text": "⚠️ Connectivity issue. Please try again."}}]

    def execute_tool(self, tool_name: str, parameters: dict):
        if tool_name not in self.tool_map:
            return f"❌ Unknown tool: {tool_name}"
        try:
            return self.tool_map[tool_name](**parameters)
        except Exception as e:
            return f"❌ Error executing '{tool_name}': {e}"

    def speak(self, text: str):
        self.is_speaking = True
        self.stop_playback_event.clear()
        def play_audio():
            try:
                audio_stream = self.elevenlabs_client.text_to_speech.convert(voice_id=self.voice_id, text=text, model_id="eleven_multilingual_v2")
                play(audio_stream, interrupt_event=self.stop_playback_event)
            except Exception as e:
                self.console.print(f"[bold red]🔇 TTS Error: {e}[/bold red]")
        playback_thread = threading.Thread(target=play_audio, daemon=True)
        playback_thread.start()
        while playback_thread.is_alive():
            if self.stop_playback_event.is_set():
                break
            time.sleep(0.1)
        self.is_speaking = False

    def interrupt_speech(self):
        if self.is_speaking:
            self.console.print("[yellow]⏹️ Speech interrupted[/yellow]")
            self.stop_playback_event.set()

    async def listen(self):
        options = LiveOptions(model="nova-2", language=self.language, smart_format=True, interim_results=True)
        try:
            dg_connection = self.deepgram_client.listen.asynclive.v("1")
            async def on_message(result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                if len(sentence.strip()) > 0:
                    self.interrupt_speech()
                if getattr(result, "is_final", False) and len(sentence.strip()) > 0:
                    await self.task_queue.put(sentence)
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            await dg_connection.start(options)
        except Exception as e:
            self.console.print(f"[bold red]🎙️ Deepgram Error: {e}[/bold red]")

    async def _process_voice_tasks(self):
        while True:
            user_command = await self.task_queue.get()
            final_response = await self.handle_command(user_command)
            await asyncio.to_thread(self.speak, text=final_response)
            self.task_queue.task_done()

    async def run_voice_agent(self):
        self.console.print(Panel("[bold cyan]🚀 Kala-Sahayak Voice Agent Online[/]", title="🖥️ System Status"))
        self.chroma_manager.clear_history()
        self.console.print("[green]Starting new session. Chat history cleared.[/green]")
        welcome_message = self.welcome_messages.get(self.language, "👋 Hello! How can I assist you?")
        await asyncio.to_thread(self.speak, text=welcome_message)
        processing_task = asyncio.create_task(self._process_voice_tasks())
        listening_task = asyncio.create_task(self.listen())
        try:
            await asyncio.gather(processing_task, listening_task)
        finally:
            self.knowledge_graph.close()

if __name__ == "__main__":
    console = Console()
    language_options = {"1": {"name": "🇮🇳 English (India)", "code": "en-IN"}, "2": {"name": "🇮🇳 हिन्दी (Hindi)", "code": "hi-IN"}}
    console.print(Panel("[bold green]🌟 Welcome to Kala-Sahayak[/]\nSelect your language:", title="🏁 Start"))
    for key, value in language_options.items():
        console.print(f"{key}. {value['name']}")
    lang_choice = input("🔢 Enter your choice (1/2): ")
    selected_language_code = language_options.get(lang_choice, {"code": "en-IN"})["code"]
    agent = KalaSahayakAgent(language=selected_language_code)
    console.print(Panel("🔊 1) Voice Mode\n⌨️ 2) Text Mode", title="🛠️ Mode Selection"))
    mode_choice = input("🔢 Enter your choice (1/2): ")

    if mode_choice == '1':
        try:
            asyncio.run(agent.run_voice_agent())
        except KeyboardInterrupt:
            print("\n👋 Voice agent shutdown by user.")
    elif mode_choice == '2':
        console.print(Panel("⌨️ Text Mode Active. Type 'quit', 'exit', or 'new session' to start over.", title="💬 Conversation"))
        agent.chroma_manager.clear_history()
        console.print("[green]Starting new session. Chat history cleared.[/green]")
        while True:
            query = input("🧑 You: ")
            if query.lower() in ["quit", "exit"]:
                console.print("[bold red]🚪 Exiting Text Mode[/bold red]")
                break
            if query.lower() == "new session":
                agent.chroma_manager.clear_history()
                console.print("[green]Starting new session. Chat history cleared.[/green]")
                continue
            response = agent.process_text_query(query)
            console.print(Panel(response, title="🤖 Kala-Sahayak", border_style="magenta"))
    else:
        console.print("[bold red]❌ Invalid choice. Please run again.[/bold red]")
