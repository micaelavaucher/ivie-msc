"""Configuration management for IVIE.

This module handles all configuration-related functionality including
reading config files, setting up paths, and managing global settings.
Only application-level configurations are managed here.
User-level configurations are handled via Streamlit session state.
"""

import os
from dotenv import load_dotenv
import configparser
import time
from urllib.parse import quote_plus

load_dotenv()

PATH_GAMELOGS = 'logs'

def load_config():
    """Load configuration from config.ini file."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def get_model_names(config):
    """Get model names from config."""
    reasoning_model_name = config['Models']['ReasoningModel']
    narrative_model_name = config['Models']['NarrativeModel']
    return reasoning_model_name, narrative_model_name

def create_log_filename():
    """Create a unique log filename based on current timestamp."""
    timestamp = time.time()
    today = time.gmtime(timestamp)
    return f"{today[0]}_{today[1]}_{today[2]}_{str(int(time.time()))[-5:]}.json"

def get_enable_rag(config):
    """Get the RAG enable setting from config."""
    return config["Options"].getboolean("EnableRAG", fallback=True)

def get_debug(config):
    """Get the debug setting from config."""
    return config["Options"].getboolean("Debug", fallback=False)

def get_database_config(config):
    """Get database settings from config."""
    db_name = config['Database']['DatabaseName']
    collection_name = config['Database']['TracesCollection']
    
    # Get credentials from environment
    mongo_user = os.getenv('MONGO_USER')
    mongo_password = os.getenv('MONGO_PASSWORD')
    mongo_cluster = os.getenv('MONGO_CLUSTER')
    
    # If full URI is provided, use it directly
    mongo_uri = os.getenv('MONGO_URI')
    
    if not mongo_uri:
        # Build URI from components with proper escaping
        if not all([mongo_user, mongo_password, mongo_cluster]):
            raise ValueError("Either MONGO_URI or (MONGO_USER, MONGO_PASSWORD, MONGO_CLUSTER) must be set in environment variables.")
        
        # Escape username and password according to RFC 3986
        escaped_user = quote_plus(mongo_user)
        escaped_password = quote_plus(mongo_password)
        
        # Build connection string
        mongo_uri = f"mongodb+srv://{escaped_user}:{escaped_password}@{mongo_cluster}/?retryWrites=true&w=majority"
    
    return mongo_uri, db_name, collection_name