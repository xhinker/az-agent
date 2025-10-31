import os
import json
from typing import Optional
import httpx

def load_server_config():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config

class LLMChat:
    '''
    Every chat object includes everything needed for one complete chat
    '''
    def __init__(
        self,
        llm_api_url:str                                 = "https://api.openai.com/v1",
        model_name:str                                  = "default",
        api_key:str                                     = "",
        system_prompt: str                              = "",
        timeout:float                                   = 10.0,
        enable_http2:bool                               = False,
        httpx_client:Optional[httpx.Client]             = None,
        httpx_async_client:Optional[httpx.AsyncClient]  = None,
    ):
        # llm model settings
        self.llm_api_url        = llm_api_url
        self.api_key            = api_key
        self.model_name         = model_name
        self.timeout            = timeout
        self.headers    = {
            "Authorization": f"Bearer {api_key}" if api_key else "",
            "Content-Type": "application/json",
        }

        # httpx settings
        self.httpx_limits = httpx.Limits(
            max_connections             = 10,
            max_keepalive_connections   = 1,
            keepalive_expiry            = 30
        )

        # use a dictionary so that avoid define it twice for client and async_client
        self.httpx_config = {
            "base_url":self.llm_api_url,
            "headers" :self.headers,
            "timeout" :self.timeout,
            "http2"   :enable_http2,
            "limits"  :self.httpx_limits
        }

        # use a external client so that avoid system running out of http threads
        self.client       = httpx_client or httpx.Client(**self.httpx_config)
        self.async_client = httpx_async_client or httpx.AsyncClient(**self.httpx_config)

        # LLM settings
        if system_prompt:
            self.messages  = [
                {"role": "system", "content": system_prompt}
            ]
        else:
            self.messages       = []

    def chat(self, message: str, system_prompt: str = "") -> str:
        """
        Send a message to the LLM and save the conversation history in self.messages
        
        Args:
            message: The user message to send
            system_prompt: Optional system prompt to set the context
            
        Returns:
            The LLM's response as a string
        """
        # Add system prompt if provided and not already in messages
        # Use this to change system prompt in the middle of a chat
        if system_prompt and (not self.messages or self.messages[0].get("role") != "system"):
            self.messages.insert(0, {"role": "system", "content": system_prompt})
        
        # Add user message to history
        self.messages.append({"role": "user", "content": message})
        
        # Prepare the request payload
        payload = {
            "model": self.model_name,
            "messages": self.messages,
            "stream": False
        }
        
        try:
            # Send request to LLM API
            response = self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            # Extract the assistant's response
            response_data = response.json()
            assistant_message = response_data["choices"][0]["message"]["content"]
            
            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error occurred: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    async def async_chat(self, message: str, system_prompt: str = "") -> str:
        """
        Send a message to the LLM asynchronously and save the conversation history in self.messages
        
        Args:
            message: The user message to send
            system_prompt: Optional system prompt to set the context
            
        Returns:
            The LLM's response as a string
        """
        print(f'input message:{message}')
        # Add system prompt if provided and not already in messages
        # Use this to change system prompt in the middle of a chat
        if system_prompt and (not self.messages or self.messages[0].get("role") != "system"):
            self.messages.insert(0, {"role": "system", "content": system_prompt})
        
        # Add user message to history
        self.messages.append({"role": "user", "content": message})
        
        # Prepare the request payload
        payload = {
            "model": self.model_name,
            "messages": self.messages,
            "stream": False
        }
        
        try:
            # Send request to LLM API asynchronously
            response = await self.async_client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            # Extract the assistant's response
            response_data = response.json()
            assistant_message = response_data["choices"][0]["message"]["content"]
            
            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error occurred: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
