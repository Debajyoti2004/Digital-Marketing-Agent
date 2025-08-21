import os
import json
import uuid
import asyncio
import threading
import traceback
from typing import TypedDict, Annotated, List, Union
from datetime import UTC
import argparse

import cohere
import config
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from rich.console import Console
from rich.panel import Panel
from mcp import ClientSession
from mcp.client.sse import sse_client

from tool_definations import get_tool_definitions
from knowledge_graph import KnowledgeGraph
from chroma_manager import ChromaDBManager
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from intent_classifier import IntentClassifier, IntentResponse

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    user_command: str
    intent: str
    cached_plan: Union[List[dict], None]
    recalled_memories: List[str]
    last_plan: Union[List[dict], None]

class KalaSahayakLangGraphAgent:
    PREAMBLE_OWNER = """
# 👑 ROLE: Kala-Sahayak (कला-सहायक) - AI Co-Founder & Strategist
You are an expert AI partner for an Indian artisan (the "owner"). Your persona is that of a proactive, data-driven co-founder. You are a strategic force multiplier with a powerful suite of tools. Your goal is to grow the artisan's business.
# 🧭 CORE WORKFLOW & DIRECTIVES
Your primary function is to achieve the owner's goals through a cyclical, stateful reasoning process. You will operate in a loop: **PLAN -> EXECUTE -> ANALYZE -> RE-PLAN**.
1.  **🤔 INTENT ANALYSIS:**
    - First, analyze the owner's message. Is it a task requiring tools (`tool_use`) or casual conversation (`general_conversation`)?
    - Use any `recalled_memories` provided for critical context.
2.  **🛠️ STRATEGIC TOOL WORKFLOW (for `tool_use`):**
    This is your most critical directive. You MUST follow this sequence precisely for every task.
    - **Initial Plan:** Formulate a plan by calling the single most logical tool to start the task (often research) OR multiple tools if they can be executed in parallel without dependencies.
    - **Execution & Analysis:** After the system executes your planned tools, it will return the results. You MUST analyze these results to inform your next step.
    - **Re-planning:** Based on the tool results, you will continue the task by generating the next set of tool calls. If the results indicate the task is complete, you will generate a final summary for the owner.
    - **Repeat:** Continue this `EXECUTE -> ANALYZE -> RE-PLAN` loop until the owner's multi-step goal is fully achieved.
3.  **💡FAILURE ANALYSIS & CORRECTION (CRITICAL):**
    - If a tool returns an error OR the user provides corrective feedback (e.g., "No, that's not right, change the price"), you must analyze the failure.
    - Your NEXT step is to generate a NEW, CORRECTED plan. In your reasoning, explicitly state what went wrong and how the new plan fixes it. Example: "The previous search was too broad. This new plan uses a more specific query to find better results."
# 🛡️ GUARDRAILS
- **Confirmation:** Before executing a final, irreversible action (e.g., `facebook_post_image`), you MUST STOP and ask the owner for confirmation with a direct text response.
- **Safety & Privacy**: Never perform harmful/illegal actions or ask for sensitive credentials.
# 💬 COMMUNICATION STYLE
- **Tone**: Encouraging, strategic, and professional.
- **Structure**: Use clear headings, bullet points, and lists. Use symbols: ✅, ⚠️, ❌, 💡, 📊, 🚀.
- **Conclusion**: Always end your final response with a summary of what was accomplished and suggest logical `Next Steps`.
"""
    PREAMBLE_CUSTOMER = """
# 🤖 ROLE: Kala-Sahayak (कला-सहायк) - Customer Support Ambassador
You are a helpful, friendly AI assistant representing an Indian artisan brand. Your persona is warm, patient, and professional. Your goal is to provide excellent customer service.
# 🧭 CORE DIRECTIVES
- **Answer Politely:** Answer customer questions using general knowledge.
- **Escalate When Necessary:** If you cannot answer or are asked to perform an action, politely state your limitation and offer to pass the message to the owner. Example: "I'm the support assistant and can't check live inventory. I can forward your request to the owner, who can help you directly. Is that okay?"
# 🛡️ GUARDRAILS
- **Privacy:** Never ask for financial information like credit card numbers.
"""
    
    def __init__(self, role: str = "owner", language="en-IN"):
        self.console = Console()
        self.cohere_client = cohere.Client(api_key=config.COHERE_API_KEY)
        self.knowledge_graph = KnowledgeGraph()
        self.chroma_manager = ChromaDBManager()
        self.role = role
        self.language = language
        self.preamble = self.PREAMBLE_OWNER if self.role == "owner" else self.PREAMBLE_CUSTOMER
        self.active_tools = get_tool_definitions() if self.role == "owner" else []
        self.mcp_session: ClientSession = None
        self.mcp_sse_client = None
        self.graph = self._build_graph()
        self.intent_classifier = IntentClassifier(model_name="gemini-1.5-pro")
        self.deepgram_client = DeepgramClient(config.DEEPGRAM_API_KEY)
        self.elevenlabs_client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
        self.voice_id = getattr(config, "ELEVENLABS_VOICE_ID", None)
        self.is_speaking = False
        self.stop_playback_event = threading.Event()
        self.task_queue = asyncio.Queue()
        self.welcome_messages = {
            "en-IN": "🙏 Hello! I'm Kala-Sahayak 🤖 — your creative & strategic ally. How can I help today?",
            "hi-IN": "🙏 नमस्ते! मैं कला-सहायक 🤖 — आपका रचनात्मक और रणनीतिक साथी। मैं आपकी कैसे मदद कर सकता हूँ?"
        }

    @classmethod
    async def create(cls, role: str = "owner", language="en-IN", server_url="http://localhost:8080"):
        agent = cls(role, language)
        sse_url = f"{server_url}/sse"
        agent.console.print(Panel(f"🔌 Connecting to MCP Tool Server via SSE at {sse_url}...", title="MCP Client"))
        try:
            agent.mcp_sse_client = sse_client(sse_url)
            read_stream, write_stream = await agent.mcp_sse_client.__aenter__()
            agent.mcp_session = ClientSession(read_stream, write_stream)
            await agent.mcp_session.initialize()
            agent.console.print(Panel(f"✅ Successfully connected to: [bold green]{agent.mcp_session.server_info.name}[/]", title="MCP Client"))
        except Exception as e:
            agent.console.print(Panel(f"❌ Failed to connect to MCP Tool Server: {e}", title="[bold red]Connection Error[/]"))
            raise
        return agent

    async def close(self):
        if self.mcp_sse_client:
            await self.mcp_sse_client.__aexit__(None, None, None)
            self.console.print(Panel("🔌 MCP SSE connection closed.", title="MCP Client"))

    def _emit_status(self, status: str):
        self.console.print(Panel(status, title="⚙️ Agent Status", border_style="bold blue", expand=False))

    def load_memories(self, state: AgentState, config: RunnableConfig):
        self._emit_status("🧠 Loading Memories...")
        user_query = state["messages"][-1].content
        session_id = config["configurable"]["thread_id"]
        allowed_speakers = ["owner", "agent"] if self.role == "owner" else ["customer", "agent"]
        recalled_memories = self.chroma_manager.retrieve_relevant_memories(
            query=user_query, session_id=session_id, allowed_speaker_types=allowed_speakers
        )
        self._emit_status(f"Recalled {len(recalled_memories)} similar memories for context.")
        if recalled_memories:
            memory_context = "\n".join(recalled_memories)
            augmented_message = HumanMessage(content=f"**Recalled Memories (for context only):**\n---\n{memory_context}\n---\n**Current User Request:**\n{user_query}")
            state["messages"][-1] = augmented_message
        return {"recalled_memories": recalled_memories, "user_command": user_query}

    def classify_intent(self, state: AgentState):
        self._emit_status("🤔 Classifying user intent...")
        user_message = state["messages"][-1].content
        if self.role == "customer" or not self.active_tools:
            self._emit_status("Intent classified as: [bold]general_conversation[/bold]")
            return {"intent": "general_conversation"}
        response: IntentResponse = self.intent_classifier.classify_intent(user_message)
        intent = response.intent
        self._emit_status(f"Intent classified as: [bold]{intent}[/bold]")
        return {"intent": intent}

    def find_strategic_plan(self, state: AgentState):
        if self.role != "owner":
            return {"cached_plan": None}
        self._emit_status("🔍 Searching Knowledge Graph for a successful plan...")
        user_command = state["user_command"]
        cached_plan = self.knowledge_graph.find_successful_plan(user_command)
        if cached_plan:
            self._emit_status("♻️ Found a relevant successful plan.")
        else:
            self._emit_status("No relevant successful plan found.")
        return {"cached_plan": cached_plan}

    def brain_adapt_plan(self, state: AgentState):
        self._emit_status("🧠⚡ Adapting cached plan...")
        user_message = state["user_command"]
        cached_plan = state["cached_plan"]
        message = f"Previous Plan: {json.dumps(cached_plan, indent=2)}\nNew Request: \"{user_message}\"\nUpdate the parameters of the previous plan to fit the new request. Output only the updated `tool_calls`."
        response = self.cohere_client.chat(message=message, model="command-r-plus", tools=self.active_tools, preamble=self.preamble)
        return {"messages": [AIMessage(content=response.text, tool_calls=response.tool_calls)]}

    def brain_generate_plan(self, state: AgentState):
        self._emit_status("💡 Generating new plan or continuing task...")
        response = self.cohere_client.chat(model="command-r-plus", chat_history=[m.model_dump() for m in state["messages"]], tools=self.active_tools, preamble=self.preamble, message="")
        last_plan = [tc.model_dump() for tc in response.tool_calls] if response.tool_calls else None
        return {"messages": [AIMessage(content=response.text, tool_calls=response.tool_calls)], "last_plan": last_plan}

    async def tool_node(self, state: AgentState):
        last_message = state["messages"][-1]
        tool_messages = []
        if not self.mcp_session:
            raise RuntimeError("MCP session not initialized. Cannot execute tools.")

        for tool_call in last_message.tool_calls:
            self._emit_status(f"📡 Calling remote tool: {tool_call['name']}...")
            try:
                result = await self.mcp_session.call_tool(
                    tool_call["name"],
                    arguments=tool_call["parameters"]
                )
                tool_messages.append(ToolMessage(content=result.content[0].text, tool_call_id=tool_call["id"]))
                self._emit_status(f"✅ Success: {tool_call['name']}")
            except Exception as e:
                error_message = f"Error calling remote tool {tool_call['name']}: {e}"
                self._emit_status(f"❌ {error_message}")
                tool_messages.append(ToolMessage(content=json.dumps({"error": error_message}), tool_call_id=tool_call["id"]))
        return {"messages": tool_messages}

    def general_conversation_node(self, state: AgentState):
        self._emit_status("💬 Engaging in general conversation...")
        user_message = state["messages"][-1]
        response = self.cohere_client.chat(message=user_message.content, model="command-r", preamble=self.preamble)
        return {"messages": [AIMessage(content=response.text)]}
        
    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("load_memories", self.load_memories)
        builder.add_node("classify_intent", self.classify_intent)
        builder.add_node("find_strategic_plan", self.find_strategic_plan)
        builder.add_node("brain_adapt_plan", self.brain_adapt_plan)
        builder.add_node("brain_generate_plan", self.brain_generate_plan)
        builder.add_node("tool_node", self.tool_node)
        builder.add_node("general_conversation_node", self.general_conversation_node)
        builder.set_entry_point("load_memories")
        builder.add_edge("load_memories", "classify_intent")
        builder.add_conditional_edges("classify_intent", lambda state: "general_conversation_node" if state["intent"] == "general_conversation" else "find_strategic_plan")
        builder.add_conditional_edges("find_strategic_plan", lambda state: "brain_adapt_plan" if state.get("cached_plan") else "brain_generate_plan")
        def should_execute_tools(state):
            return "tool_node" if state["messages"][-1].tool_calls else END
        builder.add_conditional_edges("brain_adapt_plan", should_execute_tools)
        builder.add_conditional_edges("brain_generate_plan", should_execute_tools)
        builder.add_edge("tool_node", "brain_generate_plan")
        builder.add_edge("general_conversation_node", END)
        memory = MemorySaver()
        return builder.compile(checkpointer=memory)

    async def get_agent_response(self, session_id: str, user_text: str, is_feedback: bool = False):
        config_run = RunnableConfig(configurable={"thread_id": session_id})
        if is_feedback:
            current_state = await self.graph.aget_state(config_run)
            current_state.messages.append(HumanMessage(content=user_text))
            stream = self.graph.astream(current_state.model_dump(), config=config_run, stream_mode="values")
        else:
            if self.role == "owner":
                self.chroma_manager.add_owner_message(content=user_text, language=self.language, session_id=session_id)
            else:
                self.chroma_manager.add_customer_message(content=user_text, language=self.language, session_id=session_id)
            initial_state = {"messages": [HumanMessage(content=user_text)]}
            stream = self.graph.astream(initial_state, config=config_run, stream_mode="values")

        final_response_text, last_plan = "Sorry, I encountered an issue.", None
        try:
            async for event in stream:
                if "messages" in event:
                    last_message = event["messages"][-1]
                    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
                        final_response_text = last_message.content
                if "last_plan" in event:
                    last_plan = event.get("last_plan")
        except Exception as e:
            final_response_text = "Sorry, there was an error processing your request."
            self.console.print(Panel(f"Agent execution error: {e}\n\n{traceback.format_exc()}", title="[bold red]Agent Error[/]", border_style="red"))
            self._emit_status("🚨 Error")

        self.chroma_manager.add_agent_message(content=final_response_text, language=self.language, session_id=session_id)
        return final_response_text, last_plan

    async def run_text_agent(self):
        self.console.print(Panel("⌨️ Text Mode Active. Type 'quit' or 'exit' to end.", title="💬 Conversation"))
        thread_id, user_command_for_session, last_plan_for_session = str(uuid.uuid4()), "", None
        while True:
            if not user_command_for_session:
                user_input = await asyncio.to_thread(self.console.input, "🧑 You: ")
                if user_input.lower() in ["quit", "exit"]:
                    self.console.print("[bold red]🚪 Exiting...[/bold red]"); self.knowledge_graph.close(); break
                user_command_for_session = user_input
                response_text, last_plan = await self.get_agent_response(thread_id, user_command_for_session)
                last_plan_for_session = last_plan
            
            self.console.print(Panel(response_text, title="🤖 Agent Response", border_style="magenta"))
            
            if self.role == "owner" and last_plan_for_session:
                feedback_input = await asyncio.to_thread(self.console.input, "👍 Was this result helpful? (yes/no or provide correction): ")
                if feedback_input.lower() in ["yes", "y"]:
                    self.knowledge_graph.store_successful_plan(user_command_for_session, last_plan_for_session)
                    self.console.print(Panel("✅ Glad I could help! Plan saved.", title="✨ Session", border_style="green"))
                    user_command_for_session, last_plan_for_session = "", None
                elif feedback_input.lower() in ["no", "n"]:
                    self.knowledge_graph.store_failed_plan(user_command_for_session, last_plan_for_session, "User was not satisfied.")
                    self.console.print(Panel("📝 Understood. Let's try a different approach.", title="🔄 Correcting", border_style="yellow"))
                    user_command_for_session, last_plan_for_session = "", None
                else:
                    self.knowledge_graph.store_failed_plan(user_command_for_session, last_plan_for_session, feedback_input)
                    self.console.print(Panel("📝 Thank you. I will try again with the new information.", title="🔄 Correcting", border_style="yellow"))
                    correction_message = f"My previous attempt was incorrect. The user provided this feedback: '{feedback_input}'. Please create a new plan."
                    response_text, last_plan = await self.get_agent_response(thread_id, correction_message, is_feedback=True)
                    last_plan_for_session = last_plan
            else:
                user_command_for_session, last_plan_for_session = "", None
    
    async def speak(self, text: str):
        self.is_speaking = True
        self.stop_playback_event.clear()
        def play_audio_thread():
            try:
                audio_stream = self.elevenlabs_client.text_to_speech.convert(voice_id=self.voice_id, text=text, model_id="eleven_multilingual_v2")
                play(audio_stream, interrupt_event=self.stop_playback_event)
            except Exception as e:
                self.console.print(f"[bold red]🔇 TTS Error: {e}[/bold red]")
            finally:
                self.is_speaking = False
        await asyncio.to_thread(threading.Thread(target=play_audio_thread, daemon=True).start)

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
                if len(sentence.strip()) > 0: self.interrupt_speech()
                if getattr(result, "is_final", False) and len(sentence.strip()) > 0: await self.task_queue.put(sentence)
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            await dg_connection.start(options)
        except Exception as e:
            self.console.print(f"[bold red]🎙️ Deepgram Error: {e}[/bold red]")

    async def _process_voice_tasks(self, thread_id: str):
        while True:
            user_command = await self.task_queue.get()
            response_text, last_plan = await self.get_agent_response(thread_id, user_command)
            await self.speak(response_text)
            
            if self.role == "owner" and last_plan:
                await self.speak("Was this result helpful?")
                feedback_command = await self.task_queue.get()
                if feedback_command.lower() in ["yes", "yep", "haan"]:
                    self.knowledge_graph.store_successful_plan(user_command, last_plan)
                    await self.speak("Great! Plan saved. What's next?")
                else:
                    self.knowledge_graph.store_failed_plan(user_command, last_plan, feedback_command)
                    await self.speak("Understood. I will try again with your feedback.")
                    correction_message = f"My previous attempt was incorrect. User feedback: '{feedback_command}'. Please create a new plan."
                    new_response, new_plan = await self.get_agent_response(thread_id, correction_message, is_feedback=True)
                    await self.speak(new_response)

    async def run_voice_agent(self):
        self.console.print(Panel("[bold cyan]🚀 Kala-Sahayak Voice Agent Online[/]", title="🖥️ System Status"))
        thread_id = str(uuid.uuid4())
        welcome_message = self.welcome_messages.get(self.language, "👋 Hello! How can I assist you?")
        await self.speak(welcome_message)
        
        processing_task = asyncio.create_task(self._process_voice_tasks(thread_id))
        listening_task = asyncio.create_task(self.listen())
        
        try:
            await asyncio.gather(processing_task, listening_task)
        finally:
            self.knowledge_graph.close()

async def main_async():
    parser = argparse.ArgumentParser(description="Kala-Sahayak AI Agent")
    parser.add_argument("--routine", type=str, help="The name of the routine to execute from routines.json.")
    args = parser.parse_args()
    console = Console()
    agent = None
    try:
        if args.routine:
            agent = await KalaSahayakLangGraphAgent.create(role="owner")
            console.print("[yellow]Routines are not yet adapted for the MCP client-server architecture.[/yellow]")
        else:
            console.print(Panel("[bold green]🌟 Welcome to the Ultimate Kala-Sahayak Agent (Interactive Mode)[/bold green]", title="🏁 Start"))
            role_options = {"1": {"name": "👑 Owner", "code": "owner"},"2": {"name": "👤 Customer", "code": "customer"}}
            console.print(Panel("[bold green]Select your role:[/bold green]"))
            for key, value in role_options.items(): console.print(f"  {key}. {value['name']}")
            role_choice = console.input("🔢 Enter your choice (1/2): ")
            selected_role = role_options.get(role_choice, {"code": "owner"})["code"]
            
            console.print(Panel("[bold green]Select Mode:[/bold green]\n  🔊 1) Voice Mode\n  ⌨️ 2) Text Mode"))
            mode_choice = console.input("🔢 Enter your choice (1/2): ")
            
            agent = await KalaSahayakLangGraphAgent.create(role=selected_role)
            agent.preamble = agent.PREAMBLE_OWNER if selected_role == "owner" else agent.PREAMBLE_CUSTOMER

            if mode_choice == '1':
                await agent.run_voice_agent()
            elif mode_choice == '2':
                await agent.run_text_agent()
            else:
                console.print("[bold red]❌ Invalid choice. Please run again.[/bold red]")
    except Exception as e:
        console.print(Panel(f"A critical error occurred: {e}\n{traceback.format_exc()}", title="[bold red]Critical Error[/]"))
    finally:
        if agent:
            await agent.close()

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n👋 Agent shutdown by user.")