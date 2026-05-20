"""
LLM Configuration for AgentOS

Primary: Quatarly API (unified Claude/GPT/Gemini gateway)
- Primary model: claude-opus-4-6-thinking
- Fallback 1: claude-sonnet-4-6thinking  
- Fallback 2: gpt-5.1
- Fallback 3: gemini-2.0-flash (if key available)
- Fallback 4: Ollama qwen2.5:3b (local, last resort)
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Quatarly LLM (Primary) - OpenAI-compatible API with Claude/GPT/Gemini
# ─────────────────────────────────────────────────────────────────────
quatarly_primary = ChatOpenAI(
    model=settings.QUATARLY_PRIMARY_MODEL,
    api_key=settings.QUATARLY_API_KEY,
    base_url=settings.QUATARLY_BASE_URL,
    temperature=0.3,
    max_retries=2,
    timeout=120,
)

quatarly_fallback_1 = ChatOpenAI(
    model=settings.QUATARLY_FALLBACK_1,
    api_key=settings.QUATARLY_API_KEY,
    base_url=settings.QUATARLY_BASE_URL,
    temperature=0.3,
    max_retries=2,
    timeout=120,
)

quatarly_fallback_2 = ChatOpenAI(
    model=settings.QUATARLY_FALLBACK_2,
    api_key=settings.QUATARLY_API_KEY,
    base_url=settings.QUATARLY_BASE_URL,
    temperature=0.3,
    max_retries=2,
    timeout=120,
)

# ─────────────────────────────────────────────────────────────────────
# Gemini LLM (Third fallback) - only if API key available
# ─────────────────────────────────────────────────────────────────────
gemini_llm = None
if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 10:
    gemini_llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
        max_retries=1,
    )

# ─────────────────────────────────────────────────────────────────────
# Ollama LLM (Last resort - local)
# ─────────────────────────────────────────────────────────────────────
ollama_llm = ChatOllama(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
    temperature=0.3,
    num_predict=512,
)

# ─────────────────────────────────────────────────────────────────────
# Main LLM with fallbacks chain:
# Quatarly Opus → Quatarly Sonnet → Quatarly GPT → Gemini (if avail) → Ollama
# ─────────────────────────────────────────────────────────────────────
fallbacks = [quatarly_fallback_1, quatarly_fallback_2]
if gemini_llm:
    fallbacks.append(gemini_llm)
fallbacks.append(ollama_llm)

llm = quatarly_primary.with_fallbacks(fallbacks)

# Separate reference for health checks
primary_llm = quatarly_primary
all_llms = [quatarly_primary, quatarly_fallback_1, quatarly_fallback_2]
if gemini_llm:
    all_llms.append(gemini_llm)
all_llms.append(ollama_llm)


async def health_check() -> bool:
    """Check if any LLM in the chain is available."""
    model_names = [
        settings.QUATARLY_PRIMARY_MODEL,
        settings.QUATARLY_FALLBACK_1, 
        settings.QUATARLY_FALLBACK_2,
        settings.GEMINI_MODEL if gemini_llm else None,
        settings.OLLAMA_MODEL
    ]
    for i, llm_instance in enumerate(all_llms):
        try:
            response = llm_instance.invoke("Say OK")
            logger.info(f"Health check passed: {model_names[i]}")
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {model_names[i]}: {e}")
    logger.error("All LLMs in chain failed health check")
    return False


async def rate_limit_delay():
    """Small delay to prevent rate limiting."""
    await asyncio.sleep(1.5)
