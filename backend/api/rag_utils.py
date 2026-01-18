import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
import asyncio
import httpx
import base64
from typing import List, Dict
import json
import logging
import numpy as np

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
EMBEDDING_MODEL = "text-embedding-004"

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1beta'})

# persistent storage for SimpleVectorDB
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "simple_vector_db.json")

class SimpleVectorDB:
    def __init__(self, persist_path: str):
        self.persist_path = persist_path
        self.data = {} # {collection_name: {"embeddings": [], "documents": [], "metadatas": [], "ids": []}}
        self.load()

    def load(self):
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, "r") as f:
                    self.data = json.load(f)
                logger.info(f"Loaded SimpleVectorDB with {len(self.data)} collections")
            except Exception as e:
                logger.error(f"Failed to load vector DB: {e}")
                self.data = {}

    def persist(self):
        try:
            with open(self.persist_path, "w") as f:
                json.dump(self.data, f)
            logger.info("SimpleVectorDB persisted to disk")
        except Exception as e:
            logger.error(f"Failed to persist vector DB: {e}")

    def get_or_create_collection(self, name: str):
        if name not in self.data:
            self.data[name] = {"embeddings": [], "documents": [], "metadatas": [], "ids": []}
        return SimpleCollection(name, self)

    def get_collection(self, name: str):
        if name not in self.data:
            raise KeyError(f"Collection {name} does not exist")
        return SimpleCollection(name, self)
    
    def list_collections(self):
        class Col:
            def __init__(self, name): self.name = name
        return [Col(name) for name in self.data.keys()]

class SimpleCollection:
    def __init__(self, name: str, db: SimpleVectorDB):
        self.name = name
        self.db = db

    def add(self, ids, embeddings, metadatas, documents):
        self.db.data[self.name]["ids"].extend(ids)
        self.db.data[self.name]["embeddings"].extend(embeddings)
        self.db.data[self.name]["metadatas"].extend(metadatas)
        self.db.data[self.name]["documents"].extend(documents)

    def query(self, query_embeddings, n_results=5):
        query_vec = np.array(query_embeddings[0])
        collection_data = self.db.data[self.name]
        
        if not collection_data["embeddings"]:
            return {"documents": [[]]}

        # Compute cosine similarity
        embeddings = np.array(collection_data["embeddings"])
        
        # Avoid division by zero
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        norm_embeddings = embeddings / norms
        
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0: query_norm = 1e-9
        norm_query = query_vec / query_norm
        
        similarities = np.dot(norm_embeddings, norm_query)
        top_indices = np.argsort(similarities)[::-1][:n_results]
        
        return {
            "documents": [[collection_data["documents"][i] for i in top_indices]]
        }

class RepositoryRAG:
    def __init__(self):
        self.vector_db = SimpleVectorDB(DB_PATH)
        
    async def get_embedding(self, text: str) -> List[float]:
        if not client:
            return [0.0] * 768 # Fallback
        
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config={"task_type": "RETRIEVAL_DOCUMENT"}
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [0.0] * 768

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks

    async def index_files(self, user_id: int, repo_full_name: str, files: Dict[str, str]):
        """Index a batch of files into SimpleVectorDB"""
        collection_name = f"user_{user_id}_{repo_full_name.replace('/', '_').replace('-', '_')}"
        logger.info(f"Indexing repository '{repo_full_name}' for user {user_id}")
        
        collection = self.vector_db.get_or_create_collection(name=collection_name)
        
        # Clear existing data for this collection before re-indexing (optional, but cleaner for sync)
        self.vector_db.data[collection_name] = {"embeddings": [], "documents": [], "metadatas": [], "ids": []}

        for path, content in files.items():
            if not content or len(content) < 10:
                continue
                
            chunks = self.chunk_text(content)
            for i, chunk in enumerate(chunks):
                embedding = await self.get_embedding(chunk)
                collection.add(
                    ids=[f"{path}_chunk_{i}"],
                    embeddings=[embedding],
                    metadatas=[{"path": path, "chunk_index": i}],
                    documents=[chunk]
                )
        
        self.vector_db.persist()
        logger.info(f"Successfully indexed and persisted repository for user {user_id}")

    async def query(self, user_id: int, repo_full_name: str, query_text: str) -> str:
        """Query the indexed repository and generate a response from a senior colleague"""
        collection_name = f"user_{user_id}_{repo_full_name.replace('/', '_').replace('-', '_')}"
        project_name = repo_full_name.split('/')[-1].replace('-', ' ').title()

        # 1. Handle very short or ambiguous general queries without RAG if needed
        # But for simplicity, we first try to see if it's a "which project" type of question
        is_ambiguous_request = any(phrase in query_text.lower() for phrase in ["which project", "what project", "about what", "context"])
        
        try:
            collection = self.vector_db.get_collection(name=collection_name)
            has_index = True
        except:
            has_index = False

        if not has_index:
            return f"Hey! I haven't indexed your repository ({project_name}) yet. Click the sync icon so I can take a look at your code!"

        query_embedding = await self.get_embedding(query_text)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        context = ""
        if results['documents'][0]:
            context = "\n---\n".join(results['documents'][0])
        
        prompt = f"""
        You are a supportive, slightly informal Senior Developer ("Senior Colleague").
        You are chatting with a junior developer about their specific project: "{project_name}".
        
        RULES:
        1. Be CONCISE. Professional humans don't write essays in chat. 2-3 short paragraphs max.
        2. Be DYNAMIC and CONVERSATIONAL. Use phrases like "Hey," "Actually," "I noticed that," "Good question."
        3. If the user's question is vague and doesn't mention "{project_name}", start by confirming you're talking about that project.
        4. If the provided context doesn't help at all, don't guess deep technical details. Just say "I'm not seeing that in the {project_name} codebase, maybe check [X]?"
        5. If the user asks what project you mean, tell them: "We're looking at your {project_name} repo."
        
        PROJECT CONTEXT (snippets from {project_name}):
        {context}
        
        USER MESSAGE: "{query_text}"
        
        RESPONSIBLE RESPONSE:
        """
        
        if not client:
            return "I'm sorry, my AI brain is a bit foggy right now. Try again in a second?"
            
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text

    async def sync_with_github(self, user_id: int, repo_full_name: str, access_token: str, db_session):
        """Fetch changes from GitHub and update index"""
        from models import User
        from sqlalchemy.future import select
        
        async with httpx.AsyncClient() as github_client:
            # 1. Get latest commit
            commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            resp = await github_client.get(commits_url, headers=headers)
            if resp.status_code != 200:
                return False
                
            commits = resp.json()
            if not commits:
                return False
                
            latest_sha = commits[0]["sha"]
            
            # 2. Check if we need to sync
            stmt = select(User).where(User.id == user_id)
            result = await db_session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user.last_indexed_commit == latest_sha:
                return True # Already up to date
                
            # 3. Fetch full repository tree (simplified for MVP: fetch files recursively)
            tree_url = f"https://api.github.com/repos/{repo_full_name}/git/trees/{latest_sha}?recursive=1"
            resp = await github_client.get(tree_url, headers=headers)
            if resp.status_code != 200:
                return False
                
            tree = resp.json().get("tree", [])
            files_to_index = {}
            
            for item in tree:
                if item["type"] == "blob":
                    path = item["path"]
                    # Skip non-code files
                    if any(path.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".html", ".css", ".md", ".json", ".java", ".cs"]):
                        # Fetch file content
                        file_resp = await github_client.get(item["url"], headers=headers)
                        if file_resp.status_code == 200:
                            content_data = file_resp.json()
                            content = base64.b64decode(content_data["content"]).decode('utf-8', errors='ignore')
                            files_to_index[path] = content
                            
            if files_to_index:
                await self.index_files(user_id, repo_full_name, files_to_index)
                
            # 4. Update user metadata
            user.last_indexed_commit = latest_sha
            await db_session.commit()
            return True

rag_engine = RepositoryRAG()
