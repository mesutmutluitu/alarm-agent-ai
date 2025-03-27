from langchain_core.language_models.llms import LLM
import requests

class OllamaLLM(LLM):
    model: str = "mistral"
    endpoint_url: str = "http://localhost:11434/api/generate"

    def _call(self, prompt: str, stop=None):
        response = requests.post(
            self.endpoint_url,
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=60
        )
        try:
            result = response.json()
            return result.get("response", response.text)
        except ValueError:
            return response.text

    @property
    def _llm_type(self) -> str:
        return "ollama"
