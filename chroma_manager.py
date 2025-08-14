import chromadb
import uuid
import json
from datetime import datetime

class ChromaDBManager:
    def __init__(self, path="./chroma_db", collection_name="kala_sahayak_chat"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def _add_message(self, role: str, content: str, language: str):
        doc_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[{"role": role, "timestamp": timestamp, "language": language}]
        )

    def add_user_message(self, content: str, language: str):
        self._add_message(role="USER", content=content, language=language)

    def add_chatbot_message(self, content: str, language: str):
        self._add_message(role="CHATBOT", content=content, language=language)

    def add_tool_message(self, call: dict, outputs: list, language: str):
        content = json.dumps({"call": call, "outputs": outputs}, default=str)
        self._add_message(role="TOOL", content=content, language=language)

    def get_formatted_history(self, limit: int = 25):
        results = self.collection.get(include=["documents", "metadatas"])
        
        if not results['ids']:
            return []

        sorted_results = sorted(zip(results['documents'], results['metadatas']), key=lambda item: item[1]['timestamp'])
        
        formatted_history = []
        for doc, meta in sorted_results:
            role = meta['role']
            if role == "USER" or role == "CHATBOT":
                formatted_history.append({"role": role, "message": doc})
            elif role == "TOOL":
                tool_data = json.loads(doc)
                formatted_history.append({"role": role, "tool_results": [tool_data]})

        return formatted_history[-limit:]

    def clear_history(self):
        self.collection.delete(where={})