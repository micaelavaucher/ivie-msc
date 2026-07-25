"""Intelligent Memory System for IVIE.

This module implements a RAG (Retrieval-Augmented Generation) system that creates
and maintains an intelligent memory of game events, allowing the system to 
retrieve relevant past memories when processing new player actions.
"""

import os
import time
from typing import List, Dict
from pathlib import Path
import jsonpickle
import numpy as np
from google import genai
from google.genai import types
import chromadb
from chromadb.config import Settings
from ..config import PATH_GAMELOGS
from src.ivie.core.world_utils import create_world_state_summary
from ..database.mongodb_handler import db_handler

os.environ["ANONYMIZED_TELEMETRY"] = "False"


class AtomicMemory:
    """Represents a single atomic memory unit from a game turn."""
    
    def __init__(self, turn_number: int, player_action: str, result_narration: str, 
                 world_state_summary: str = "", metadata: Dict = None):
        self.turn_number = turn_number
        self.player_action = player_action
        self.result_narration = result_narration
        self.world_state_summary = world_state_summary
        self.metadata = metadata or {}
        self.timestamp = time.time()
        
    def to_text(self) -> str:
        memory_text = f"Turn {self.turn_number}:\n"
        memory_text += f"Player Action: {self.player_action}\n"
        memory_text += f"Result: {self.result_narration}"
        
        if self.world_state_summary:
            memory_text += f"\nContext: {self.world_state_summary}"
            
        return memory_text
    
    def to_dict(self) -> Dict:
        # Flatten metadata to primitive types for storage
        flattened_metadata = {}
        if self.metadata:
            for key, value in self.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    flattened_metadata[key] = value
                else:
                    flattened_metadata[key] = str(value)
        
        return {
            "turn_number": self.turn_number,
            "player_action": self.player_action,
            "result_narration": self.result_narration,
            "world_state_summary": self.world_state_summary,
            "timestamp": self.timestamp,
            **flattened_metadata  # Flatten metadata into main dict
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AtomicMemory':
        # Extract standard fields
        turn_number = data.get("turn_number", 0)
        player_action = data.get("player_action", "")
        result_narration = data.get("result_narration", "")
        world_state_summary = data.get("world_state_summary", "")
        
        # Reconstruct metadata from any extra fields
        excluded_keys = {"turn_number", "player_action", "result_narration", "world_state_summary", "timestamp"}
        metadata = {k: v for k, v in data.items() if k not in excluded_keys}
        
        memory = cls(
            turn_number=turn_number,
            player_action=player_action,
            result_narration=result_narration,
            world_state_summary=world_state_summary,
            metadata=metadata
        )
        
        # Restore timestamp if available
        if "timestamp" in data:
            memory.timestamp = data["timestamp"]
            
        return memory

class EmbeddingService:
    """Service for generating embeddings using Gemini API."""
    
    def __init__(self, api_key: str = None):
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
        
        self.client = genai.Client(api_key=api_key)
        self.types = types
    
    def generate_embedding(self, text: str) -> List[float]:
        try:
            result = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=self.types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=768
                )
            )
            # Extract the embedding values from the response
            embedding_values = result.embeddings[0].values
            
            # Normalize embeddings for 768 dimensions (as recommended in docs)
            embedding_array = np.array(embedding_values)
            normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
            
            return normalized_embedding.tolist()
        except Exception as e:
            print(f"⚠️ Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 768

class MemoryStore:
    """Vector database for storing and retrieving memories."""
    
    def __init__(self, world_id: str, persist_directory: str = None):
        self.world_id = world_id
        self.persist_directory = persist_directory or str(Path(PATH_GAMELOGS) / "memory_db")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Create or get collection
        collection_name = f"memories_{self.world_id}"
        try:
            self.collection = self.client.get_collection(collection_name)
        except ValueError:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": f"Game memories for world {world_id}"}
            )
    
    def add_memory(self, memory: AtomicMemory, embedding: List[float]):
        memory_id = f"turn_{memory.turn_number}_{int(memory.timestamp)}"
        
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[memory.to_text()],
            metadatas=[memory.to_dict()]
        )
    
    def search_memories(self, query_embedding: List[float], top_k: int = 3) -> List[AtomicMemory]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            memories = []
            if results['metadatas'] and results['metadatas'][0]:
                for metadata in results['metadatas'][0]:
                    memories.append(AtomicMemory.from_dict(metadata))
            
            return memories
        except Exception as e:
            print(f"⚠️ Error searching memories: {e}")
            return []

class IntelligentMemorySystem:
    """Main memory system that coordinates embedding and retrieval."""
    
    def __init__(self, world_id: str, api_key: str = None):
        self.world_id = world_id
        self.embedding_service = EmbeddingService(api_key)
        self.memory_store = MemoryStore(world_id)
        self.last_turn_processed = 0
    
    def ingest_memory(self, turn_number: int, player_action: str, 
                     result_narration: str, world_state_summary: str = "") -> bool:
        try:
            # Create atomic memory
            memory = AtomicMemory(
                turn_number=turn_number,
                player_action=player_action,
                result_narration=result_narration,
                world_state_summary=world_state_summary
            )
            
            # Generate embedding
            memory_text = memory.to_text()
            embedding = self.embedding_service.generate_embedding(memory_text)
            
            # Store in vector database
            self.memory_store.add_memory(memory, embedding)
            
            self.last_turn_processed = turn_number
            print(f"🧠 Memory ingested for Turn {turn_number}")
            return True
            
        except Exception as e:
            print(f"⚠️ Error ingesting memory for Turn {turn_number}: {e}")
            return False
    
    def retrieve_relevant_memories(self, current_action: str, top_k: int = 3) -> List[AtomicMemory]:
        try:
            # Generate embedding for current action
            query_embedding = self.embedding_service.generate_embedding(current_action)
            
            # Search for relevant memories
            relevant_memories = self.memory_store.search_memories(query_embedding, top_k)
            
            if relevant_memories:
                print(f"🔍 Retrieved {len(relevant_memories)} relevant memories")
                for i, memory in enumerate(relevant_memories, 1):
                    print(f"  {i}. Turn {memory.turn_number}: {memory.player_action[:50]}...")
            else:
                print(f"🔍 No relevant memories found for this action")
            
            return relevant_memories
            
        except Exception as e:
            print(f"⚠️ Error retrieving memories: {e}")
            return []
    
    def format_memories_for_prompt(self, memories: List[AtomicMemory], language: str = 'en') -> str:
        if not memories:
            return ""
        
        if language == 'es':
            header = "## Recuerdos Relevantes del Pasado\n"
            header += "Aquí hay algunos eventos pasados que podrían ser relevantes para la acción actual:\n"
        else:
            header = "## Relevant Past Memories\n"
            header += "Here are some past events that might be relevant to the current action:\n"
        
        formatted_memories = []
        for memory in memories:
            memory_line = f"- Turn {memory.turn_number}: {memory.result_narration}"
            formatted_memories.append(memory_line)
        
        return header + "\n".join(formatted_memories) + "\n"
    
    def load_memories_from_db(self, world_id: str) -> int:
        if not db_handler:
            print("⚠️ Database handler not available, cannot load memories.")
            return 0

        try:
            game_trace = db_handler.get_trace_by_world_id(world_id)
            if not game_trace or "turns" not in game_trace:
                print(f"🧠 No existing trace found in DB for world {world_id}")
                return 0

            memories_loaded = 0
            language = game_trace.get("language", "en") # Get language for the summary function

            # Sort turns by turn number to process them chronologically
            sorted_turns = sorted(game_trace["turns"].items(), key=lambda item: int(item[0]))

            for turn_key, turn_data in sorted_turns:
                turn_number = int(turn_key)
                if turn_number == 0 or turn_number <= self.last_turn_processed:
                    continue

                player_action = turn_data.get("user_input")
                result_narration = turn_data.get("narration")
                world_state_str = turn_data.get("previous_symbolic_world_state")

                if player_action and result_narration and world_state_str:
                    # Re-hydrate the world object from the stored JSON string
                    world_at_turn = jsonpickle.decode(world_state_str)

                    world_state_summary = create_world_state_summary(
                        world=world_at_turn,
                        player_action=player_action,
                        language=language
                    )

                    success = self.ingest_memory(
                        turn_number=turn_number,
                        player_action=player_action,
                        result_narration=result_narration,
                        world_state_summary=world_state_summary
                    )
                    if success:
                        memories_loaded += 1

            print(f"🧠 Loaded {memories_loaded} memories from database for world {world_id} with rich context.")
            return memories_loaded

        except Exception as e:
            print(f"⚠️ Error loading memories from database: {e}")
            import traceback
            traceback.print_exc()
            return 0

def create_memory_system(world_id: str, api_key: str = None) -> IntelligentMemorySystem:
    return IntelligentMemorySystem(world_id, api_key)
