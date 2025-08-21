import chromadb
import uuid
import json
from datetime import datetime
from typing import List
from rich import print as rprint
from rich.panel import Panel

class ChromaDBManager:
    def __init__(self, path="./chroma_db", collection_name="kala_sahayak_memory"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        rprint(Panel.fit("[green]✅ ChromaDB Manager Initialized[/green]"))

    def add_owner_message(self, session_id: str, content: str, language: str):
        self._add_message(session_id=session_id, role="USER", content=content, language=language, speaker_type="owner")

    def add_customer_message(self, session_id: str, content: str, language: str):
        self._add_message(session_id=session_id, role="USER", content=content, language=language, speaker_type="customer")

    def add_agent_message(self, session_id: str, content: str, language: str):
        self._add_message(session_id=session_id, role="CHATBOT", content=content, language=language, speaker_type="agent")

    def add_tool_message(self, session_id: str, calls: list, outputs: list, language: str):
        content = json.dumps({"calls": calls, "outputs": outputs}, default=str)
        self._add_message(session_id=session_id, role="TOOL", content=content, language=language, speaker_type="agent")

    def retrieve_relevant_memories(self, session_id: str, query: str, allowed_speaker_types: List[str], k: int = 5) -> List[str]:
        if self.collection.count() == 0:
            return []
            
        where_clause = {
            "$and": [
                {"session_id": session_id},
                {"speaker_type": {"$in": allowed_speaker_types}}
            ]
        }
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where_clause
            )
            recalled_docs = results.get('documents', [[]])[0]
            return recalled_docs if recalled_docs else []
        except Exception as e:
            rprint(Panel(f"[red]❌ ChromaDB query failed:[/red] {e}", title="ChromaDB Error"))
            return []

    def get_formatted_history(self, session_id: str, limit: int = 25):
        if self.collection.count() == 0:
            return []

        results = self.collection.get(
            where={"session_id": session_id},
            include=["documents", "metadatas"]
        )
        
        if not results['ids']:
            return []

        sorted_results = sorted(zip(results['documents'], results['metadatas']), key=lambda item: item[1]['timestamp'])
        
        formatted_history = []
        for doc, meta in sorted_results:
            role = meta.get('role', 'USER')
            if role in ["USER", "CHATBOT"]:
                formatted_history.append({"role": role, "message": doc})
            elif role == "TOOL":
                try:
                    tool_data = json.loads(doc)
                    formatted_history.append({
                        "role": "TOOL",
                        "tool_results": [{"call": call, "outputs": out} for call, out in zip(tool_data.get("calls", []), tool_data.get("outputs", []))]
                    })
                except json.JSONDecodeError:
                    continue

        return formatted_history[-limit:]

    def clear_session_history(self, session_id: str):
        try:
            self.collection.delete(where={"session_id": session_id})
            rprint(Panel(f"[yellow]🧹 Cleared history for session:[/yellow] {session_id}", title="ChromaDB Maintenance"))
        except Exception as e:
            rprint(Panel(f"[red]❌ Failed to clear history for session {session_id}:[/red] {e}", title="ChromaDB Error"))

    def _add_message(self, session_id: str, role: str, content: str, language: str, speaker_type: str):
        doc_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        metadata = {
            "session_id": session_id,
            "role": role, 
            "timestamp": timestamp, 
            "language": language,
            "speaker_type": speaker_type
        }

        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata]
        )