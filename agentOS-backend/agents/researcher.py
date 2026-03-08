from tavily import TavilyClient
from core.llm import llm, rate_limit_delay
from config import settings

_SUMMARIZE_SYSTEM = (
    "You are a research summarizer. Given these web search results, "
    "write a clear factual summary of key findings relevant to the query. "
    "Write in plain paragraphs. Be concise. No bullet points. No markdown."
)


class ResearchAgent:
    def __init__(self):
        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    async def run(self, query: str) -> str:
        # ── Search ──────────────────────────────────────────────────
        try:
            results = self.client.search(query, max_results=5)
            numbered_results = ""
            for i, r in enumerate(results["results"], 1):
                numbered_results += f"{i}. {r['title']}\n{r['content']}\n\n"
        except Exception as e:
            print(f"[Researcher] Tavily error: {e}")
            return "Research unavailable. Using LLM knowledge only."

        # ── Summarise ───────────────────────────────────────────────
        prompt = (
            f"{_SUMMARIZE_SYSTEM}\n\n"
            f"Query: {query}\n\n"
            f"Search Results:\n{numbered_results}"
        )
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()
