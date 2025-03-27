from langchain.llms.base import LLM
import requests

class OllamaLLM(LLM):
    model: str = "mistral"
    endpoint_url: str = "http://localhost:2030"

    def _call(self, prompt: str, stop=None):
        response = requests.post(
            self.endpoint_url,
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=30
        )
        result = response.json()
        return result.get("response", "")

    @property
    def _llm_type(self) -> str:
        return "ollama"