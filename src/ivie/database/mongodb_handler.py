import pymongo
from pymongo.mongo_client import MongoClient
from ..config import load_config, get_database_config

class MongoHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoHandler, cls).__new__(cls)
            try:
                config = load_config()
                uri, db_name, collection_name = get_database_config(config)
                if not uri:
                    raise ValueError("MONGO_URI not found in environment variables.")

                cls._instance.client = MongoClient(uri)
                cls._instance.db = cls._instance.client[db_name]
                cls._instance.collection = cls._instance.db[collection_name]
                
                # Test connection with ping
                cls._instance.client.admin.command('ping')
                print("✅ Successfully connected to MongoDB.")
            except Exception as e:
                print(f"❌ Failed to connect to MongoDB: {e}")
                cls._instance = None
        return cls._instance

    def initialize_trace(self, initial_log_entry: dict):
        try:
            result = self.collection.insert_one(initial_log_entry)
            return result.inserted_id
        except Exception as e:
            print(f"Error initializing trace in MongoDB: {e}")
            return None

    def add_turn_to_trace(self, world_id: str, turn_number: int, turn_data: dict):
        try:
            query = {"world_id": world_id}
            update = {"$set": {f"turns.{turn_number}": turn_data}}
            self.collection.update_one(query, update)
        except Exception as e:
            print(f"Error adding turn {turn_number} to trace {world_id}: {e}")

    def get_trace_by_world_id(self, world_id: str):
        try:
            return self.collection.find_one({"world_id": world_id})
        except Exception as e:
            print(f"Error retrieving trace for world_id {world_id}: {e}")
            return None
    
    def trace_exists(self, world_id: str) -> bool:
        try:
            count = self.collection.count_documents({"world_id": world_id})
            return count > 0
        except Exception as e:
            print(f"Error checking trace existence for world_id {world_id}: {e}")
            return False

# Create a single, importable instance of the handler
db_handler = MongoHandler()