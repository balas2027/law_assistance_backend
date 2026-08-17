from anthropic import Anthropic
from app.core.config import settings

class LLMClient:
    def __init__(self) -> None:
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

    def generate(self, prompt: str, system: str = None) -> str:
        if not self.client:
            return "Anthropic client not initialized. Please set ANTHROPIC_API_KEY."
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                system=system,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error communicating with Anthropic API: {str(e)}"

llm_client = LLMClient()
