from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from pathlib import Path

# Import services
from src.services.logging_services import setup_logger
from src.services.config_loader_services import config_loader

class GPTServices:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)
        self.logger = setup_logger(self.__class__.__name__)

        
    # GPTServices class
    def gpt_services(self, text: str, model: str, prompt: str, temperature: float):
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            temperature= 0.1,
        )
        return json.loads(response.choices[0].message.content)

