import logging
import openai
from src.config import LLMConfig, load_config

logger = logging.getLogger(__name__)

class LLMClient:
    """
    An OpenAI-compatible LLM client.
    """
    def __init__(self, config: LLMConfig = None):
        self.config = config or load_config()
        self.client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )

    def complete(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        """
        Generates a completion for the given prompt.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise e
