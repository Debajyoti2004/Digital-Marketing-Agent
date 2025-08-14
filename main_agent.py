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
        self.language = language
        self.voice_id = getattr(config, "ELEVENLABS_VOICE_ID", None)
        self.is_speaking = False
        self.stop_playback_event = threading.Event()
        self.task_queue = asyncio.Queue()
        self.chat_history = []
        self.welcome_messages = {
            "en-IN": "🙏 Hello! I’m Kala-Sahayak 🤖 — your creative & strategic ally. How can I help today?",
            "hi-IN": "🙏 नमस्ते! मैं कला-सहायक 🤖 — आपका रचनात्मक और रणनीतिक साथी। मैं आपकी कैसे मदद कर सकता हूँ?"
        }

        self.preamble = """
🧭 <Identity>
You are Kala-Sahayak — a multilingual, culturally-aware AI for Indian artisans, entrepreneurs, and teams. You excel at Digital Marketing 📢, E-Commerce 🛒, Creative Design 🎨, Social Media 📱, Product Strategy 🎯, Market Research 🔍, Tech Troubleshooting 🛠️, and Business Ops 📊. You adapt tone to the user’s level (beginner 🐣, intermediate 🚀, expert 🏆) and stay practical, ethical, and results-driven.
</Identity>

⚖️ <Guardrails>
1) Safety & Legality: Decline harmful/illegal/unsafe requests and suggest compliant alternatives. 
2) Privacy: Never expose secrets, credentials, or sensitive personal data.
3) Confirm Before Impact: Ask for confirmation before posting, publishing, messaging, or changing live data.
4) Truthful & Verifiable: Prefer concrete data, cite sources when available, and flag assumptions.
5) Cultural Sensitivity: Use inclusive, respectful language; localize examples for India when helpful.

🧠 <Reasoning & Planning>
1) Clarify → Plan → Execute → Verify → Summarize. Ask targeted questions only when essential.
2) Decompose complex tasks into steps; sequence logically; avoid using artifacts before they exist.
3) Offer 2–3 strategy options with pros/cons when trade-offs exist.
4) Tool Failure Protocol: retry once (if safe), switch tool or method, then summarize fallback plan.
5) When blocked, propose workarounds, templates, or manual steps the user can run.

🗺️ <Scenario Playbooks>
• Business/Marketing 📢: craft ICP, positioning, messaging, campaign plans (objectives, channels, cadence, KPIs), budgets, and measurement plans.
• E-Commerce 🛒: product listings, pricing, inventory notes, keyword bullets, A+ copy, promo calendars.
• Creative 🎨: generate briefs, moodboards (described), copy variants, hooks, captions, CTAs; iterate fast.
• Social Media 📱: post calendars, cross-platform repurposing, hashtags, alt text, compliance checks.
• Research 🔍: competitor snapshots, SWOTs, trend scans, insights with prioritized next steps.
• Tech 🛠️: debugging checklists, stepwise fixes, minimal reproducible examples, and crisp code snippets.
• Support 🚨: acknowledge, isolate issue, quick win first, then robust fix; confirm resolution.
• Multilingual 🌏: translate/transcreate with tone preservation; note formal vs casual register.

💬 <Communication>
1) Structure outputs with headings, bullets, and numbered steps. Keep it crisp; bold key actions.
2) Use symbols for status: ✅ success, ⚠️ caution, ❌ error, 🔄 retry, 🧩 tip, 🗂️ summary, 📌 note.
3) End with a short “Next Steps” list when appropriate.
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
        self.chat_history.append({"role": "USER", "message": user_command})

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
                self.chat_history.append({"role": "CHATBOT", "message": final_response_text})
                break

            result = await asyncio.to_thread(self.execute_tool, tool_name, params)

            if isinstance(result, (dict, list)):
                result_str = json.dumps(result, indent=2, default=str)
                display_result = Syntax(result_str, "json", theme="monokai", line_numbers=True)
            else:
                display_result = str(result)

            self.console.print(Panel(display_result, title=f"📦 Tool Result • {tool_name}", border_style="green", expand=False))

            if isinstance(result, dict) and result.get("error"):
                plan_successful = False
                final_response_text = f"❌ Tool `{tool_name}` failed: {result.get('error')}"
                self.chat_history.append({"role": "CHATBOT", "message": final_response_text})
                break

            self.chat_history.append({"role": "TOOL", "tool_results": [{"call": step, "outputs": [result]}]})

        if not final_response_text:
            try:
                summary_response = await asyncio.to_thread(
                    self.cohere_client.chat,
                    message="Summarize for the user what was accomplished. Use symbols, list key results, and next steps. Keep it concise.",
                    chat_history=self.chat_history,
                    model="command-r"
                )
                final_response_text = summary_response.text
                self.chat_history.append({"role": "CHATBOT", "message": final_response_text})
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
                chat_history=self.chat_history,
                tools=self.tools,
                model="command-r",
                preamble=self.preamble
            )
            return response.tool_calls or (
                [{"tool_name": "speak_direct", "parameters": {"text": response.text}}] if response.text else []
            )
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
                audio_stream = self.elevenlabs_client.text_to_speech.convert(
                    voice_id=self.voice_id, text=text, model_id="eleven_multilingual_v2")
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

    language_options = {
        "1": {"name": "🇮🇳 English (India)", "code": "en-IN"},
        "2": {"name": "🇮🇳 हिन्दी (Hindi)", "code": "hi-IN"}
    }

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
        console.print(Panel("⌨️ Text Mode Active. Type 'quit' or 'exit' to end.", title="💬 Conversation"))
        while True:
            query = input("🧑 You: ")
            if query.lower() in ["quit", "exit"]:
                console.print("[bold red]🚪 Exiting Text Mode[/bold red]")
                break
            response = agent.process_text_query(query)
            console.print(Panel(response, title="🤖 Kala-Sahayak", border_style="magenta"))
    else:
        console.print("[bold red]❌ Invalid choice. Please run again.[/bold red]")
