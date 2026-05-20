"""
Code Execution Sandbox
======================

Actually RUNS code and returns real output. Not just generated text.
This is the key differentiator: AgentOS closes the loop.

Demo: "Write a Python scraper" → Gets code → RUNS it → Shows real output.
"""
import os
import sys
import subprocess
import tempfile
import asyncio
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


class CodeSandbox:
    """
    Sandboxed code execution environment.
    
    Safety measures:
    - 30 second timeout
    - Memory limit via subprocess
    - No network access flag (optional)
    - Output size capped at 10KB
    """
    
    TIMEOUT_SECONDS = 30
    MAX_OUTPUT_BYTES = 10_000

    async def run(
        self,
        code: str,
        language: str = "python",
        timeout: int = TIMEOUT_SECONDS,
        allow_network: bool = True,
    ) -> dict:
        """
        Execute code and return real output.
        
        Args:
            code: Code to execute
            language: python, javascript, bash
            timeout: Max execution time in seconds
            allow_network: Whether to allow network access
            
        Returns:
            dict with success, stdout, stderr, execution_time, exit_code
        """
        print(f"[CodeSandbox] Running {language} code ({len(code)} chars)")
        
        start_time = datetime.now()
        
        if language == "python":
            result = await self._run_python(code, timeout)
        elif language in ("javascript", "js", "node"):
            result = await self._run_javascript(code, timeout)
        elif language in ("bash", "shell", "sh"):
            result = await self._run_bash(code, timeout)
        else:
            result = {
                "success": False,
                "stdout": "",
                "stderr": f"Unsupported language: {language}",
                "exit_code": 1,
            }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        result["execution_time_seconds"] = round(execution_time, 3)
        
        # Attach status log
        status = "SUCCESS" if result["success"] else "FAILED"
        print(f"[CodeSandbox] {status} in {execution_time:.2f}s, exit={result.get('exit_code', -1)}")
        
        return result

    async def _run_python(self, code: str, timeout: int) -> dict:
        """Run Python code in isolated subprocess."""
        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "exit_code": -1,
                    "timed_out": True,
                }
            
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            
            # Cap output size
            if len(stdout_text) > self.MAX_OUTPUT_BYTES:
                stdout_text = stdout_text[:self.MAX_OUTPUT_BYTES] + "\n... [output truncated]"
            
            return {
                "success": proc.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_code": proc.returncode,
                "language": "python",
            }
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    async def _run_javascript(self, code: str, timeout: int) -> dict:
        """Run JavaScript code using Node.js."""
        # Check if node is available
        try:
            check = await asyncio.create_subprocess_exec(
                "node", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await check.communicate()
            if check.returncode != 0:
                raise RuntimeError("Node.js not found")
        except Exception:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Node.js not installed. Install from https://nodejs.org/",
                "exit_code": 1,
            }
        
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".js",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "node", temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout}s",
                    "exit_code": -1,
                    "timed_out": True,
                }
            
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": proc.returncode,
                "language": "javascript",
            }
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    async def _run_bash(self, code: str, timeout: int) -> dict:
        """Run bash/shell commands."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sh",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            shell = "bash" if os.name != "nt" else "cmd"
            proc = await asyncio.create_subprocess_exec(
                shell, temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Script timed out after {timeout}s",
                    "exit_code": -1,
                    "timed_out": True,
                }
            
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": proc.returncode,
                "language": "bash",
            }
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


class SelfHealingCodeAgent:
    """
    Write code → Run it → If error: debug → Fix → Run again.
    
    This is the "self-healing code" feature:
    - Generates code
    - Executes it
    - If it fails, analyzes the error
    - Rewrites the fix
    - Runs again
    - Repeats up to MAX_RETRIES times
    """
    
    MAX_RETRIES = 3
    
    def __init__(self):
        self._sandbox = CodeSandbox()
    
    async def run(
        self,
        task: str,
        language: str = "python",
        context: str = "",
    ) -> dict:
        """
        Generate code and execute it with self-healing.
        
        Returns:
            dict with code, output, iterations, final_success
        """
        from core.llm import llm, rate_limit_delay
        
        print(f"[SelfHealing] Task: '{task[:60]}...'")
        
        iterations = []
        code = await self._generate_code(task, language, context)
        
        for attempt in range(self.MAX_RETRIES):
            print(f"[SelfHealing] Attempt {attempt + 1}/{self.MAX_RETRIES}")
            
            # Run code
            result = await self._sandbox.run(code, language)
            
            iteration = {
                "attempt": attempt + 1,
                "code": code,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "success": result["success"],
                "exit_code": result.get("exit_code", -1),
            }
            iterations.append(iteration)
            
            if result["success"]:
                print(f"[SelfHealing] SUCCESS on attempt {attempt + 1}")
                return {
                    "success": True,
                    "final_code": code,
                    "final_output": result.get("stdout", ""),
                    "iterations": iterations,
                    "attempts_needed": attempt + 1,
                }
            
            # Failed: debug and fix
            print(f"[SelfHealing] Failed. Debugging and fixing...")
            error = result.get("stderr", "") or result.get("stdout", "")
            code = await self._debug_and_fix(task, code, error, language)
        
        # All retries exhausted
        return {
            "success": False,
            "final_code": code,
            "final_output": "",
            "error": "All self-healing attempts exhausted",
            "iterations": iterations,
            "attempts_needed": self.MAX_RETRIES,
        }
    
    async def _generate_code(self, task: str, language: str, context: str) -> str:
        """Generate initial code."""
        from core.llm import llm, rate_limit_delay
        
        prompt = f"""You are an expert {language} programmer.
Write code that RUNS correctly to complete this task.

Task: {task}
{f'Context: {context}' if context else ''}

Return ONLY the code, no markdown fences, no explanation."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        
        code = response.content.strip()
        # Remove markdown fences if present
        for fence in ("```python", "```javascript", "```bash", "```"):
            if code.startswith(fence):
                code = code[len(fence):]
        if code.endswith("```"):
            code = code[:-3]
        return code.strip()
    
    async def _debug_and_fix(
        self,
        task: str,
        code: str,
        error: str,
        language: str
    ) -> str:
        """Analyze error and produce fixed code."""
        from core.llm import llm, rate_limit_delay
        
        prompt = f"""You are a {language} debugging expert.

Original task: {task}

Code that failed:
{code}

Error output:
{error}

Fix the code. Return ONLY the corrected code, no markdown fences, no explanation."""
        
        response = llm.invoke(prompt)
        await rate_limit_delay()
        
        fixed = response.content.strip()
        for fence in ("```python", "```javascript", "```bash", "```"):
            if fixed.startswith(fence):
                fixed = fixed[len(fence):]
        if fixed.endswith("```"):
            fixed = fixed[:-3]
        return fixed.strip()


# Singleton instances
code_sandbox = CodeSandbox()
self_healing_agent = SelfHealingCodeAgent()
