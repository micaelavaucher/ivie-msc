"""Load models to use them as a narrator and a common-sense oracle in the IVIE pipeline."""
import time
import google.genai as genai
from google.genai import types
from google.genai.errors import ServerError
import replicate
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_llm(model_name: str = "gemini-3.5-flash") -> object:

    google_models = ["gemini-1.0-pro", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash",
                     "gemini-3-flash-preview", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite",
                     "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest"]
    replicate_models = ["meta/meta-llama-3-70b", "meta/meta-llama-3-70b-instruct"]
    openai_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

    model = None

    if model_name in google_models:
        model = GeminiModel(model_name=model_name)
    elif model_name in replicate_models:
        model = ReplicateModel(API_key="REPLICATE_API_TOKEN", model_name=model_name)
    elif model_name in openai_models:
        model = OpenAIModel(model_name=model_name)

    return model


class ReplicateModel():
    def __init__ (self, API_key:str, model_name:str = "meta/meta-llama-3-70b-instruct") -> None:
        self.temperature = 0.7
        self.model_name = model_name

    def prompt_model(self,system_msg: str, user_msg:str) -> str:
        

        system_instructions = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_msg}<|eot_id|><|start_header_id|>user<|end_header_id|>"

        input = {
            "top_p": 0.1,
            "min_tokens": 0,
            "temperature": self.temperature,
            "prompt": user_msg,
            "prompt_template": system_instructions + "\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        }

        output = replicate.run(self.model_name,input=input)
        
        return "".join(output)

class GeminiModel():
    def __init__ (self, model_name:str = "gemini-3.5-flash") -> None:
        
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def prompt_model(self, system_msg: str, user_msg: str, retry_attempts: int = 3, delay_seconds: int = 2) -> str:
        
        full_prompt = system_msg + "\n\n" + user_msg
        for attempt in range(retry_attempts):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        top_p=0.9,
                        max_output_tokens=6144,
                    ),
                )
                
                response_text = response.text.strip()
                
                return response_text
            except ServerError as e:
                if hasattr(e, 'error') and hasattr(e.error, 'code') and e.error.code == 503:
                    print(f"[WARN] Modelo sobrecargado. Intento {attempt+1}/{retry_attempts}")
                    time.sleep(delay_seconds)
                elif str(e).startswith('503 UNAVAILABLE'):
                    print(f"[WARN] Modelo sobrecargado. Intento {attempt+1}/{retry_attempts}")
                    time.sleep(delay_seconds)
                else:
                    print(f"[ERROR] Otro error con el modelo: {e}")
                    break
            except Exception as general_error:
                print(f"[ERROR] Error inesperado: {general_error}")
                if attempt == retry_attempts - 1:  # If it's the last attempt
                    break
                time.sleep(delay_seconds)
                
        return "⚠️ El modelo está sobrecargado o no respondió. Por favor, intentá nuevamente."
    
    def prompt_model_structured(self, prompt: str, response_schema, max_retries: int = 3, delay_seconds: int = 2):
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        response_mime_type="application/json",
                        top_p=0.9,
                        max_output_tokens=32768,
                        response_schema=response_schema,
                    ),
                )
                
                # Clean the response text before parsing
                response_text = response.text.strip()
                
                # Remove any markdown code block markers if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                if not self._is_json_complete(response_text):
                    print(f"Attempt {attempt + 1}: JSON appears truncated, retrying...")
                    continue

                # Parse the JSON response
                parsed_response = json.loads(response_text)
                return parsed_response
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error on attempt {attempt + 1}: {e}")
                if 'response' in locals():
                    print(f"Raw response: {response.text[:500]}...")
                if attempt == max_retries - 1:
                    print("Max retries reached. Returning empty result.")
                    return self._get_empty_response_for_schema(response_schema)
                else:
                    print(f"Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(delay_seconds)
                    
            except ServerError as e:
                if str(e).startswith('503 UNAVAILABLE'):
                    print(f"[WARN] Modelo sobrecargado. Intento {attempt+1}/{max_retries}")
                    time.sleep(delay_seconds)
                else:
                    print(f"[ERROR] Error del servidor en generación estructurada: {e}")
                    if attempt == max_retries - 1:
                        return self._get_empty_response_for_schema(response_schema)
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                print(f"Unexpected error in structured output generation: {e}")
                if attempt == max_retries - 1:
                    return self._get_empty_response_for_schema(response_schema)
                else:
                    print(f"Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(delay_seconds)

    def _is_json_complete(self, json_text: str) -> bool:
        if not json_text.strip():
            return False
    
        # Count braces and brackets
        open_braces = json_text.count('{')
        close_braces = json_text.count('}')
        open_brackets = json_text.count('[')
        close_brackets = json_text.count(']')
        
        # Basic check: should have matching braces/brackets
        return (open_braces == close_braces and 
                open_brackets == close_brackets and
                json_text.strip().endswith('}'))

    def _get_empty_response_for_schema(self, response_schema):
        # Generate an empty response that matches the expected schema structure
        try:
            # If the schema has a 'properties' field (typical for JSON schema)
            if hasattr(response_schema, 'properties') or (isinstance(response_schema, dict) and 'properties' in response_schema):
                return {}
            # For Pydantic models, try to create an empty instance
            elif hasattr(response_schema, 'model_validate'):
                return response_schema().model_dump()
            else:
                return {}
        except:
            return {}


class OpenAIModel():
    def __init__(self, model_name: str = "gpt-4o-mini") -> None:
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.model_name = model_name
        self.temperature = 0.7

    def prompt_model(self, system_msg: str, user_msg: str, retry_attempts: int = 3, delay_seconds: int = 2) -> str:
        for attempt in range(retry_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
                    temperature=self.temperature,
                    max_tokens=6144,
                    top_p=0.9,
                )
                
                response_text = response.choices[0].message.content.strip()
                return response_text
                
            except Exception as e:
                error_str = str(e)
                # Check for rate limiting or server errors
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    print(f"[WARN] Rate limit exceeded. Attempt {attempt+1}/{retry_attempts}")
                    time.sleep(delay_seconds * (2 ** attempt))  # Exponential backoff
                elif "502" in error_str or "503" in error_str or "504" in error_str:
                    print(f"[WARN] Server error. Attempt {attempt+1}/{retry_attempts}")
                    time.sleep(delay_seconds)
                else:
                    print(f"[ERROR] OpenAI API error: {e}")
                    if attempt == retry_attempts - 1:
                        break
                    time.sleep(delay_seconds)
                
        return "⚠️ The OpenAI model is overloaded or did not respond. Please try again."

    def prompt_model_structured(self, prompt: str, response_schema, max_retries: int = 3, delay_seconds: int = 2):
        for attempt in range(max_retries):
            try:
                response = self.client.responses.parse(
                    model=self.model_name,
                    input=[
                        {"role": "user", "content": prompt}
                    ],
                    text_format=response_schema,
                    temperature=self.temperature,
                    max_output_tokens=8192,
                    top_p=0.9,
                )
                
                # Extract the parsed response directly
                parsed_response = response.output_parsed
                
                # Convert Pydantic model to dict if needed
                if hasattr(parsed_response, 'model_dump'):
                    return parsed_response.model_dump()
                else:
                    return parsed_response
                
            except Exception as e:
                error_str = str(e)
                
                # Check if the model doesn't support structured output, fall back to JSON mode
                if "not supported" in error_str.lower() or "invalid" in error_str.lower():
                    print(f"[INFO] Model {self.model_name} doesn't support responses.parse, falling back to JSON mode...")
                    return self._fallback_json_mode(prompt, response_schema, max_retries, delay_seconds)
                
                # Handle rate limiting
                elif "rate_limit" in error_str.lower() or "429" in error_str:
                    print(f"[WARN] Rate limit exceeded in structured generation. Attempt {attempt+1}/{max_retries}")
                    time.sleep(delay_seconds * (2 ** attempt))
                else:
                    print(f"Unexpected error in structured output generation: {e}")
                    if attempt == max_retries - 1:
                        print("Falling back to JSON mode...")
                        return self._fallback_json_mode(prompt, response_schema, max_retries, delay_seconds)
                    else:
                        print(f"Retrying... ({attempt + 2}/{max_retries})")
                        time.sleep(delay_seconds)

    def _fallback_json_mode(self, prompt: str, response_schema, max_retries: int = 3, delay_seconds: int = 2):
        for attempt in range(max_retries):
            try:
                # Convert Pydantic schema to OpenAI format if needed
                if hasattr(response_schema, 'model_json_schema'):
                    schema = response_schema.model_json_schema()
                else:
                    schema = response_schema

                # Use JSON mode fallback
                enhanced_prompt = f"{prompt}\n\nPlease respond with valid JSON that matches this schema:\n{json.dumps(schema, indent=2)}"
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=8192,
                    response_format={"type": "json_object"}
                )

                response_text = response.choices[0].message.content.strip()
                
                # Clean the response text before parsing
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                if not self._is_json_complete(response_text):
                    print(f"Attempt {attempt + 1}: JSON appears truncated, retrying...")
                    continue

                # Parse the JSON response
                parsed_response = json.loads(response_text)
                return parsed_response
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error on attempt {attempt + 1}: {e}")
                if 'response' in locals():
                    print(f"Raw response: {response.choices[0].message.content[:500]}...")
                if attempt == max_retries - 1:
                    print("Max retries reached. Returning empty result.")
                    return self._get_empty_response_for_schema(response_schema)
                else:
                    print(f"Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                error_str = str(e)
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    print(f"[WARN] Rate limit exceeded in JSON fallback. Attempt {attempt+1}/{max_retries}")
                    time.sleep(delay_seconds * (2 ** attempt))
                else:
                    print(f"Unexpected error in JSON fallback: {e}")
                    if attempt == max_retries - 1:
                        return self._get_empty_response_for_schema(response_schema)
                    else:
                        print(f"Retrying... ({attempt + 2}/{max_retries})")
                        time.sleep(delay_seconds)

    def _is_json_complete(self, json_text: str) -> bool:
        if not json_text.strip():
            return False
    
        # Count braces and brackets
        open_braces = json_text.count('{')
        close_braces = json_text.count('}')
        open_brackets = json_text.count('[')
        close_brackets = json_text.count(']')
        
        # Basic check: should have matching braces/brackets
        return (open_braces == close_braces and 
                open_brackets == close_brackets and
                json_text.strip().endswith('}'))

    def _get_empty_response_for_schema(self, response_schema):
        """Generate an empty response that matches the expected schema structure."""
        try:
            # If the schema has a 'properties' field (typical for JSON schema)
            if hasattr(response_schema, 'properties') or (isinstance(response_schema, dict) and 'properties' in response_schema):
                return {}
            # For Pydantic models, try to create an empty instance
            elif hasattr(response_schema, 'model_validate'):
                return response_schema().model_dump()
            else:
                return {}
        except:
            return {}
