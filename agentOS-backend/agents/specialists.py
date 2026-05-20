"""
Specialist Agents - All domain-specific agents for end-to-end workflows.

This file contains:
- Content Agents: Writer, Editor, Summarizer
- Code Agents: CodeGen, Debugger, TestGen, CodeReviewer
- Research Agents: LiteratureAgent, CitationAgent, FactChecker  
- Data Agents: DataAnalyzer, Visualizer, Cleaner
- Document Agents: DocGenerator, SlideGenerator

These enable complete end-to-end workflows like "write a research paper" 
→ literature search → writing → citations → PDF export.
"""
import json
from typing import Optional
from core.llm import llm, rate_limit_delay


# ─────────────────────────────────────────────────────────────────────
# CONTENT AGENTS
# ─────────────────────────────────────────────────────────────────────

class WriterAgent:
    """Creates written content - articles, papers, essays, reports."""
    
    _SYSTEM_PROMPT = """You are a skilled writer. Create high-quality, well-structured content.
    - Use clear, concise language appropriate to the audience
    - Structure with proper headings and logical flow
    - Support claims with evidence where appropriate
    - Maintain consistent tone throughout
    Return ONLY the content, no meta-commentary."""

    async def run(self, task: str, context: str = "") -> str:
        prompt = f"{self._SYSTEM_PROMPT}\n\n"
        if context:
            prompt += f"Context:\n{context}\n\n"
        prompt += f"Task: {task}"
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


class EditorAgent:
    """Edits and improves existing content - grammar, clarity, style."""
    
    _SYSTEM_PROMPT = """You are an expert editor. Improve content while preserving the author's voice.
    - Fix grammatical errors and punctuation
    - Improve sentence flow and readability
    - Enhance clarity and precision
    - Apply consistent formatting
    Return ONLY the edited content, no explanations."""

    async def run(self, task: str, content: str) -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Original content to edit:
{content}

Edit request: {task}

Return ONLY the edited content."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


class SummarizerAgent:
    """Creates summaries - TL;DR, key points, executive summaries."""
    
    _SYSTEM_PROMPT = """You are an expert summarizer. Create concise, accurate summaries.
    - Extract key points and main ideas
    - Keep it brief but comprehensive
    - Use bullet points for clarity when appropriate
    - Preserve critical information
    Return ONLY the summary, no preamble."""

    async def run(self, content: str, style: str = "tldr") -> str:
        style_instructions = {
            "tldr": "Create a TL;DR: one paragraph summarizing the essence",
            "bullet": "Create bullet-point key takeaways",
            "executive": "Create an executive summary suitable for leadership",
        }
        
        prompt = f"""{self._SYSTEM_PROMPT}

{style_instructions.get(style, style_instructions['tldr'])}

Content to summarize:
{content}

Return ONLY the summary."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


# ─────────────────────────────────────────────────────────────────────
# CODE AGENTS
# ─────────────────────────────────────────────────────────────────────

class CodeGenAgent:
    """Generates code - full files, functions, classes, projects."""
    
    _SYSTEM_PROMPT = """You are an expert coder. Write clean, working, production-quality code.
    - Use modern best practices for the language
    - Include proper error handling
    - Add docstrings and comments
    - Return ONLY code inside a ```python (or language) block.
    - No explanation outside the code block."""

    async def run(self, task: str, context: str = "", language: str = "python") -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Language: {language}

Task: {task}
"""
        if context:
            prompt += f"\nContext:\n{context}"
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        
        # Extract code block
        content = response.content.strip()
        return self._extract_code(content, language)
    
    def _extract_code(self, text: str, language: str) -> str:
        """Extract code from markdown block."""
        fence = f"```{language}"
        if fence in text:
            start = text.find(fence) + len(fence)
            end = text.find("```", start)
            return text[start:end].strip()
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        return text


class DebuggerAgent:
    """Debugs code - analyzes errors, suggests fixes, applies corrections."""
    
    _SYSTEM_PROMPT = """You are an expert debugger. Analyze code errors and provide fixes.
    - Identify the root cause of the error
    - Explain what's wrong in simple terms
    - Provide a corrected code snippet
    - If the error is in a long file, show only the relevant fix
    Return JSON: {"root_cause": "...", "explanation": "...", "fixed_code": "..."}"""

    async def run(self, code: str, error: str) -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Code with error:
```
{code}
```

Error message:
{error}

Provide the fix."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


class TestGenAgent:
    """Generates unit tests and test cases."""
    
    _SYSTEM_PROMPT = """You are a test engineer. Write comprehensive unit tests.
    - Cover edge cases and error conditions
    - Use pytest/assert style
    - Make tests independent and repeatable
    - Return ONLY code inside a ```python block.
    - No explanation outside the code block."""

    async def run(self, code: str, test_framework: str = "pytest") -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Code to test:
```
{code}
```

Generate tests using {test_framework}."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return self._extract_code(response.content, "python")


class CodeReviewAgent:
    """Reviews code for issues - bugs, security, best practices."""
    
    _SYSTEM_PROMPT = """You are a senior code reviewer. Analyze code for issues.
    Look for:
    - Bugs and logic errors
    - Security vulnerabilities
    - Code smells and readability issues
    - Performance problems
    - Missing error handling
    
    Return JSON:
    {{"issues": [{{"severity": "high|medium|low", "type": "...", "location": "...", "description": "...", "suggestion": "..."}}], "overall_quality": 0.0-1.0, "recommendations": ["..."]}}
    No markdown, no text outside JSON."""

    async def run(self, code: str) -> str:
        prompt = f"{self._SYSTEM_PROMPT}\n\nCode to review:\n```\n{code}\n```"
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


# ─────────────────────────────────────────────────────────────────────
# RESEARCH AGENTS  
# ─────────────────────────────────────────────────────────────────────

class LiteratureAgent:
    """Finds academic papers and research."""
    
    _SYSTEM_PROMPT = """You are an academic research assistant. Find relevant papers.
    - Search for papers from top venues (NeurIPS, ICML, ICLR, ACL, etc.)
    - Prioritize recent papers (2022-2026)
    - Include arXiv links when available
    Return JSON: {{"papers": [{{"title": "...", "authors": "...", "year": ..., "venue": "...", "summary": "..."}}]}}"""

    async def run(self, topic: str, max_results: int = 5) -> str:
        from tavily import TavilyClient
        from config import settings
        
        # Use Tavily for web search
        try:
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            results = client.search(topic, max_results=max_results)
            
            papers = []
            for r in results.get("results", [])[:max_results]:
                papers.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:200],
                })
            
            return json.dumps({"papers": papers})
        except Exception as e:
            # Fallback to LLM
            prompt = f"{self._SYSTEM_PROMPT}\n\nTopic: {topic}\n\nFind relevant papers."
            response = llm.invoke(prompt)
            await rate_limit_delay()
            return response.content.strip()


class CitationAgent:
    """Formats citations and creates bibliographies."""
    
    _SYSTEM_PROMPT = """You are a citation expert. Format references in proper citation style.
    Supported formats: APA, MLA, Chicago, IEEE, Harvard.
    Return ONLY the formatted citations, one per line, no numbering unless requested.
    No explanation, no preamble."""

    async def run(self, sources: str, style: str = "APA") -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Citation style: {style}

Source information:
{sources}

Format these citations in {style} style."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


class FactCheckerAgent:
    """Verifies factual claims and cross-references with sources."""
    
    _SYSTEM_PROMPT = """You are a fact-checker. Verify claims against reliable sources.
    - Check if factual claims are accurate
    - Flag potential misinformation
    - Provide supporting source URLs where possible
    
    Return JSON:
    {{"verified_claims": [{{"claim": "...", "status": "verified|unverified|false", "evidence": "..."}}], "overall_reliability": 0.0-1.0}}
    No markdown, no extra text."""

    async def run(self, text: str) -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Text to fact-check:
{text}

Verify each claim."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


# ─────────────────────────────────────────────────────────────────────
# DATA AGENTS
# ─────────────────────────────────────────────────────────────────────

class DataAnalyzerAgent:
    """Analyzes data - statistics, trends, insights."""
    
    _SYSTEM_PROMPT = """You are a data analyst. Analyze datasets and extract insights.
    - Calculate relevant statistics (mean, median, std, correlations)
    - Identify trends and patterns
    - Provide actionable insights
    - Use plain language, avoid jargon
    Return JSON with analysis results where appropriate."""

    async def run(self, data: str, analysis_type: str = "general") -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Data to analyze:
{data}

Analysis type: {analysis_type}
(specify: statistical, trend, correlation, summary, etc.)"""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


class VisualizerAgent:
    """Creates visualizations - charts, graphs, plots."""
    
    _SYSTEM_PROMPT = """You are a data visualization expert. Create charts and graphs.
    - Recommend appropriate chart types for the data
    - Write Python code using matplotlib or plotly
    - Make visualizations clear and professional
    - Return ONLY code inside a ```python block.
    - No explanation outside the code block."""

    async def run(self, data: str, chart_type: str = "auto") -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Data for visualization:
{data}

Recommended chart type: {chart_type}

Generate visualization code."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return self._extract_code(response.content, "python")


class DataCleanerAgent:
    """Cleans data - deduplication, normalization, fixes."""
    
    _SYSTEM_PROMPT = """You are a data cleaning expert. Clean and preprocess data.
    - Identify and remove duplicates
    - Handle missing values appropriately
    - Normalize formats (dates, numbers, strings)
    - Fix inconsistencies
    Return cleaned data or Python code to clean it."""

    async def run(self, data: str, operations: list[str] = None) -> str:
        ops = operations or ["deduplicate", "normalize", "handle_missing"]
        
        prompt = f"""{self._SYSTEM_PROMPT}

Data to clean:
{data}

Apply operations: {', '.join(ops)}

Clean and return the result."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


# ─────────────────────────────────────────────────────────────────────
# DOCUMENT AGENTS
# ─────────────────────────────────────────────────────────────────────

class DocGeneratorAgent:
    """Generates documents - PDF, HTML, Markdown."""
    
    _SYSTEM_PROMPT = """You are a document generation expert. Create formatted documents.
    - Generate markdown that can be converted to PDF
    - Use proper formatting and structure
    - Include headers, sections, and appropriate styling
    Return the document content ready for export."""

    async def run(self, content: str, format: str = "markdown") -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Content to format:
{content}

Output format: {format}

Generate the formatted document."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


class SlideGeneratorAgent:
    """Creates presentations - PowerPoint, slides."""
    
    _SYSTEM_PROMPT = """You are a presentation expert. Create slide content.
    - Create concise, impactful slides
    - Include title, bullet points, and notes where appropriate
    - Structure for a professional presentation
    - Return in a format easy to convert to slides (markdown with clear slide breaks)
    Return ONLY the slide content."""

    async def run(self, topic: str, num_slides: int = 5) -> str:
        prompt = f"""{self._SYSTEM_PROMPT}

Topic: {topic}
Number of slides: {num_slides}

Create presentation slides."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        return response.content.strip()


# ─────────────────────────────────────────────────────────────────────
# FACTORY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────

def get_agent(agent_name: str):
    """
    Factory function to get an agent instance by name.
    
    Usage:
        agent = get_agent("writer")
        result = await agent.run(task, context)
    """
    agents = {
        "writer": WriterAgent,
        "editor": EditorAgent,
        "summarizer": SummarizerAgent,
        "coder": CodeGenAgent,
        "debugger": DebuggerAgent,
        "tester": TestGenAgent,
        "code_reviewer": CodeReviewAgent,
        "literature_agent": LiteratureAgent,
        "citation_agent": CitationAgent,
        "fact_checker": FactCheckerAgent,
        "analyzer": DataAnalyzerAgent,
        "visualizer": VisualizerAgent,
        "cleaner": DataCleanerAgent,
        "doc_generator": DocGeneratorAgent,
        "slide_generator": SlideGeneratorAgent,
    }
    
    agent_class = agents.get(agent_name)
    if agent_class is None:
        raise ValueError(f"Unknown agent: {agent_name}. Available: {list(agents.keys())}")
    
    return agent_class()


# ─────────────────────────────────────────────────────────────────────
# ENHANCED DOCUMENT AGENTS - REAL FILE OUTPUT
# ─────────────────────────────────────────────────────────────────────

class RealDocGeneratorAgent:
    """Generates REAL PDF/DOCX files, not just text."""
    
    async def run(self, content: str, task_id: str = "", title: str = "Document", format: str = "pdf") -> dict:
        """Generate actual file and return download info."""
        from agents.file_generator import get_file_generator
        from datetime import datetime
        
        if not task_id:
            task_id = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        generator = get_file_generator(format)
        return await generator.run(content, task_id, title)


class RealSlideGeneratorAgent:
    """Creates REAL PowerPoint files."""
    
    async def run(self, topic: str, num_slides: int = 5, task_id: str = "") -> dict:
        """Generate actual PPTX file."""
        from agents.file_generator import pptx_generator
        from core.llm import llm, rate_limit_delay
        from datetime import datetime
        
        if not task_id:
            task_id = f"slides_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generate content first
        prompt = f"""Create {num_slides} slides about: {topic}

Format: ## Title then bullet points.
Use --- between slides.
Be concise and professional."""

        response = llm.invoke(prompt)
        await rate_limit_delay()
        
        return await pptx_generator.run(response.content.strip(), task_id, topic)


class CodeExecutorAgent:
    """Actually runs code and returns real output."""
    
    async def run(self, task: str, language: str = "python") -> dict:
        from agents.code_sandbox import code_sandbox
        from agents.specialists import CodeGenAgent
        
        # First generate code
        codegen = CodeGenAgent()
        code = await codegen.run(task, language=language)
        
        # Then execute it
        result = await code_sandbox.run(code, language)
        
        return {
            "task": task,
            "generated_code": code,
            "execution_result": result,
        }


class SelfHealingCodeAgent:
    """Code that heals itself - generates, runs, fixes, repeats."""
    
    async def run(self, task: str, language: str = "python") -> dict:
        from agents.code_sandbox import self_healing_agent
        return await self_healing_agent.run(task, language)
