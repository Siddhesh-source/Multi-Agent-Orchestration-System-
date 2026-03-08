from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from config import settings
import asyncio

gemini_llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.3,
    max_retries=1,
)

ollama_llm = ChatOllama(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
    temperature=0.3,
    num_predict=512,
)

# Primary LLM is Gemini, fallback is Ollama
llm = gemini_llm.with_fallbacks([ollama_llm])

async def health_check() -> bool:
    try:
        response = llm.invoke("Say OK")
        return True
    except Exception as e:
        print(f"Health check failed for both Gemini and Ollama fallback: {e}")
        return False

async def rate_limit_delay():
    # Small delay. If Gemini rate limits, it will throw an exception and Langchain will automatically fall back to Ollama.
    await asyncio.sleep(1.5)
