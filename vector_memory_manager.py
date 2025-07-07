import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

# Vector database imports
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Pinecone not installed. Install with: pip install pinecone-client")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("ChromaDB not installed. Install with: pip install chromadb")

logger = logging.getLogger(__name__)

class VectorMemoryManager:
    """
    Manages AI memory and context using vector databases
    Supports both Pinecone (cloud) and ChromaDB (local)
    """
    
    def __init__(self):
        self.db_type = os.getenv('VECTOR_DB_TYPE', 'chroma').lower()
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'multilingual-e5-large')
        self.dimension = int(os.getenv('VECTOR_DIMENSION', '1024'))
        
        if self.db_type == 'pinecone' and PINECONE_AVAILABLE:
            self._init_pinecone()
        elif self.db_type == 'chroma' and CHROMA_AVAILABLE:
            self._init_chroma()
        else:
            raise ValueError(f"Vector database '{self.db_type}' not available or not installed")
    
    def _init_pinecone(self):
        """Initialize Pinecone vector database"""
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            
            # Get index
            index_name = os.getenv('PINECONE_INDEX_NAME', 'danny-bot-context')
            
            self.index = self.pc.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")
            
            # Initialize encoder as None - will be lazy-loaded when needed to avoid blocking
            self.encoder = None
            self._encoder_loading = False  # Track if encoder is being loaded
            logger.info("SentenceTransformer will be lazy-loaded when needed to avoid blocking Discord")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    def _init_chroma(self):
        """Initialize ChromaDB vector database"""
        try:
            persist_dir = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db')
            
            self.chroma_client = chromadb.Client(Settings(
                persist_directory=persist_dir,
                anonymized_telemetry=False
            ))
            
            # Create collections
            self.conversations = self.chroma_client.get_or_create_collection(
                name="conversations",
                metadata={"description": "User conversation history"}
            )
            self.personalities = self.chroma_client.get_or_create_collection(
                name="personalities", 
                metadata={"description": "Custom AI personalities"}
            )
            self.user_progress = self.chroma_client.get_or_create_collection(
                name="user_progress",
                metadata={"description": "User progress and analytics"}
            )
            
            logger.info("Connected to ChromaDB")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def _get_encoder(self):
        """Lazy-load the SentenceTransformer encoder to avoid blocking Discord event loop"""
        if self.encoder is not None:
            return self.encoder
        
        if self._encoder_loading:
            # If another coroutine is already loading, wait a bit and check again
            await asyncio.sleep(0.1)
            return self.encoder
        
        try:
            self._encoder_loading = True
            logger.info("Lazy-loading SentenceTransformer encoder...")
            
            # Import and initialize in a thread to avoid blocking
            import concurrent.futures
            
            def load_encoder():
                try:
                    from sentence_transformers import SentenceTransformer
                    return SentenceTransformer('all-MiniLM-L6-v2')
                except ImportError:
                    logger.warning("SentenceTransformer not available")
                    return None
            
            # Run in executor to avoid blocking
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(load_encoder)
                self.encoder = future.result(timeout=30)  # 30 second timeout
                
            if self.encoder:
                logger.info("SentenceTransformer encoder loaded successfully (384-dim, will pad to 1024)")
            else:
                logger.warning("Failed to load SentenceTransformer, using simple embeddings")
                
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}")
            self.encoder = None
        finally:
            self._encoder_loading = False
            
        return self.encoder
    
    async def store_conversation(self, user_id: int, conversation_text: str, 
                               session_type: str, score: Optional[int] = None,
                               personality_type: Optional[str] = None) -> bool:
        """Store conversation for future context"""
        try:
            metadata = {
                "user_id": str(user_id),
                "session_type": session_type,
                "personality_type": personality_type or "unknown",
                "timestamp": datetime.now().isoformat(),
                "score": score or 0,
                "text_length": len(conversation_text)
            }
            
            if self.db_type == 'pinecone':
                # Generate embeddings for the conversation text
                vector_id = f"conv_{user_id}_{int(datetime.now().timestamp())}"
                
                # Try to get encoder (lazy-loaded)
                encoder = await self._get_encoder()
                if encoder:
                    # Use SentenceTransformer to generate embeddings and pad to 1024
                    embedding = encoder.encode([conversation_text])[0].tolist()
                    # Pad to 1024 dimensions if needed
                    if len(embedding) < self.dimension:
                        embedding.extend([0.0] * (self.dimension - len(embedding)))
                    elif len(embedding) > self.dimension:
                        embedding = embedding[:self.dimension]
                else:
                    # Simple fallback: create a basic embedding based on text length and content
                    import hashlib
                    text_hash = hashlib.md5(conversation_text.encode()).hexdigest()
                    embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, min(len(text_hash), 32), 2)]
                    # Pad or truncate to match dimension
                    if len(embedding) < self.dimension:
                        embedding.extend([0.1] * (self.dimension - len(embedding)))
                    else:
                        embedding = embedding[:self.dimension]
                
                self.index.upsert(
                    vectors=[{
                        "id": vector_id,
                        "values": embedding,
                        "metadata": {
                            **metadata, 
                            "conversation_text": conversation_text[:1000]  # Truncate if too long
                        }
                    }]
                )
                
            elif self.db_type == 'chroma':
                # ChromaDB handles embeddings automatically
                vector_id = f"conv_{user_id}_{int(datetime.now().timestamp())}"
                
                self.conversations.add(
                    documents=[conversation_text],
                    metadatas=[metadata],
                    ids=[vector_id]
                )
            
            logger.info(f"Stored conversation for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            return False
    
    async def get_user_context(self, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """Get relevant past conversations for context"""
        try:
            if self.db_type == 'pinecone':
                # Query with metadata filter using a simple query vector
                # Try to get encoder (lazy-loaded)
                encoder = await self._get_encoder()
                if encoder:
                    query_vector = encoder.encode(["user conversation history"])[0].tolist()
                    # Pad to 1024 dimensions if needed
                    if len(query_vector) < self.dimension:
                        query_vector.extend([0.0] * (self.dimension - len(query_vector)))
                    elif len(query_vector) > self.dimension:
                        query_vector = query_vector[:self.dimension]
                else:
                    # Simple query vector
                    query_vector = [0.1] * self.dimension
                    
                results = self.index.query(
                    vector=query_vector,
                    filter={"user_id": str(user_id)},
                    top_k=limit,
                    include_metadata=True
                )
                
                return {
                    "conversations": [
                        {
                            "text": match.get("metadata", {}).get("conversation_text", ""),
                            "score": match.get("metadata", {}).get("score", 0),
                            "session_type": match.get("metadata", {}).get("session_type", ""),
                            "timestamp": match.get("metadata", {}).get("timestamp", "")
                        }
                        for match in results.get("matches", [])
                    ]
                }
                
            elif self.db_type == 'chroma':
                results = self.conversations.query(
                    query_texts=[""],
                    where={"user_id": str(user_id)},
                    n_results=limit
                )
                
                return {
                    "conversations": [
                        {
                            "text": doc,
                            "score": meta.get("score", 0),
                            "session_type": meta.get("session_type", ""),
                            "timestamp": meta.get("timestamp", "")
                        }
                        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
                    ]
                }
            
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            return {"conversations": []}
    
    async def store_custom_personality(self, user_id: int, personality_name: str, 
                                     prompt: str, description: str) -> bool:
        """Store user-created AI personalities"""
        try:
            metadata = {
                "user_id": str(user_id),
                "personality_name": personality_name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "prompt_length": len(prompt)
            }
            
            if self.db_type == 'pinecone':
                vector_id = f"personality_{user_id}_{personality_name.replace(' ', '_')}"
                
                # Store the full prompt with metadata
                self.index.upsert(
                    vectors=[{
                        "id": vector_id,
                        "values": f"{personality_name} {description} {prompt}",
                        "metadata": {**metadata, "full_prompt": prompt}
                    }]
                )
                
            elif self.db_type == 'chroma':
                vector_id = f"personality_{user_id}_{personality_name.replace(' ', '_')}"
                
                self.personalities.add(
                    documents=[prompt],
                    metadatas=[{**metadata, "full_prompt": prompt}],
                    ids=[vector_id]
                )
            
            logger.info(f"Stored personality '{personality_name}' for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store personality: {e}")
            return False
    
    async def search_personalities(self, query: str, user_id: Optional[int] = None, 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Search for personalities by description or name"""
        try:
            filter_dict = {"user_id": str(user_id)} if user_id else {}
            
            if self.db_type == 'pinecone':
                results = self.index.query(
                    vector=query,
                    filter=filter_dict,
                    top_k=limit,
                    include_metadata=True
                )
                
                return [
                    {
                        "name": match.get("metadata", {}).get("personality_name", ""),
                        "description": match.get("metadata", {}).get("description", ""),
                        "prompt": match.get("metadata", {}).get("full_prompt", ""),
                        "created_at": match.get("metadata", {}).get("created_at", ""),
                        "similarity": match.get("score", 0)
                    }
                    for match in results.get("matches", [])
                ]
                
            elif self.db_type == 'chroma':
                results = self.personalities.query(
                    query_texts=[query],
                    where=filter_dict,
                    n_results=limit
                )
                
                return [
                    {
                        "name": meta.get("personality_name", ""),
                        "description": meta.get("description", ""),
                        "prompt": meta.get("full_prompt", ""),
                        "created_at": meta.get("created_at", ""),
                        "similarity": distance
                    }
                    for meta, distance in zip(results["metadatas"][0], results["distances"][0])
                ]
            
        except Exception as e:
            logger.error(f"Failed to search personalities: {e}")
            return []
    
    async def get_user_library(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all personalities created by a user"""
        return await self.search_personalities("", user_id=user_id, limit=50)
    
    async def store_user_progress(self, user_id: int, progress_data: Dict[str, Any]) -> bool:
        """Store user progress and achievements"""
        try:
            metadata = {
                "user_id": str(user_id),
                "progress_type": progress_data.get("type", "general"),
                "timestamp": datetime.now().isoformat(),
                **progress_data
            }
            
            progress_text = json.dumps(progress_data)
            
            if self.db_type == 'pinecone':
                vector_id = f"progress_{user_id}_{int(datetime.now().timestamp())}"
                
                self.index.upsert(
                    vectors=[{
                        "id": vector_id,
                        "values": progress_text,
                        "metadata": metadata
                    }]
                )
                
            elif self.db_type == 'chroma':
                vector_id = f"progress_{user_id}_{int(datetime.now().timestamp())}"
                
                self.user_progress.add(
                    documents=[progress_text],
                    metadatas=[metadata],
                    ids=[vector_id]
                )
            
            logger.info(f"Stored progress data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store progress: {e}")
            return False
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            # Get recent conversations
            context = await self.get_user_context(user_id, limit=10)
            
            # Calculate stats
            total_sessions = len(context["conversations"])
            avg_score = sum(conv["score"] for conv in context["conversations"]) / max(total_sessions, 1)
            
            # Get personality count
            personalities = await self.get_user_library(user_id)
            
            return {
                "total_sessions": total_sessions,
                "average_score": round(avg_score, 1),
                "custom_personalities": len(personalities),
                "recent_activity": context["conversations"][:3],
                "favorite_personalities": [p["name"] for p in personalities[:3]]
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {
                "total_sessions": 0,
                "average_score": 0,
                "custom_personalities": 0,
                "recent_activity": [],
                "favorite_personalities": []
            }
    
    async def cleanup_old_data(self, days_old: int = 30) -> bool:
        """Clean up old conversation data"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            if self.db_type == 'pinecone':
                # Pinecone cleanup would require querying and deleting
                # This is more complex and should be implemented based on specific needs
                logger.info("Pinecone cleanup not implemented - consider manual cleanup")
                
            elif self.db_type == 'chroma':
                # ChromaDB cleanup
                logger.info(f"Cleaning up data older than {days_old} days")
                # Implementation would depend on ChromaDB version
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False

# Test function
async def test_vector_memory():
    """Test the vector memory system"""
    try:
        memory = VectorMemoryManager()
        
        # Test storing a conversation
        success = await memory.store_conversation(
            user_id=12345,
            conversation_text="User practiced with Owl personality, worked on objection handling",
            session_type="practice_owl",
            score=85,
            personality_type="owl"
        )
        print(f"Store conversation: {'✅' if success else '❌'}")
        
        # Test retrieving context
        context = await memory.get_user_context(12345)
        print(f"Get context: {'✅' if context['conversations'] else '❌'}")
        
        # Test storing personality
        success = await memory.store_custom_personality(
            user_id=12345,
            personality_name="Tough Negotiator",
            prompt="You are a tough negotiator who challenges every point...",
            description="A demanding customer who needs strong persuasion"
        )
        print(f"Store personality: {'✅' if success else '❌'}")
        
        # Test searching personalities
        personalities = await memory.search_personalities("negotiator", user_id=12345)
        print(f"Search personalities: {'✅' if personalities else '❌'}")
        
        print("✅ Vector memory system test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_vector_memory()) 