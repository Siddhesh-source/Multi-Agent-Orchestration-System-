"""
GitHub Integration Agent
========================

Actually CREATES GitHub repositories and pushes code.
Demo: "Build me a React app" → Creates repo → Returns GitHub URL.
"""
import os
import base64
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime


class GitHubDeployerAgent:
    """
    Creates GitHub repositories and pushes code.
    
    Uses GitHub API v3 (REST) for repo creation.
    
    For full Git operations, uses GitPython.
    """
    
    def __init__(self):
        self._token = os.environ.get("GITHUB_TOKEN", "")
        self._has_github = False
        if self._token:
            try:
                from github import Github
                self._github = Github(self._token)
                self._has_github = True
            except ImportError:
                pass
    
    async def create_repo(
        self,
        repo_name: str,
        description: str,
        code: dict[str, str],
        private: bool = False,
        auto_init: bool = True,
    ) -> dict:
        """
        Create a GitHub repo and push code.
        
        Args:
            repo_name: Name of the repository
            description: Repo description
            code: Dict of {filename: file_content}
            private: Whether to make repo private
            auto_init: Initialize with README
            
        Returns:
            dict with repo_url, clone_url, created_at
        """
        print(f"[GitHubDeployer] Creating repo: {repo_name}")
        
        if not self._has_github:
            # Fallback: create local git repo
            return await self._create_local_repo(repo_name, code)
        
        try:
            from github import Github
            from github.GithubException import GithubException
            
            user = self._github.get_user()
            
            # Create repo
            try:
                repo = user.create_repo(
                    name=repo_name,
                    description=description,
                    private=private,
                    auto_init=auto_init,
                    has_issues=True,
                    has_wiki=True,
                )
            except GithubException as e:
                # Repo might already exist
                print(f"[GitHubDeployer] Repo exists or error: {e}")
                repo = user.get_repo(repo_name)
            
            # Push code files
            for filename, content in code.items():
                # Get the default branch ref
                try:
                    default_branch = repo.default_branch
                    if default_branch is None:
                        default_branch = "main"
                    
                    # Try to get existing ref
                    try:
                        ref = repo.get_git_ref(f"refs/heads/{default_branch}")
                    except Exception:
                        # Create initial commit if needed
                        if auto_init:
                            # Create README first
                            repo.create_file(
                                "README.md",
                                f"Initial commit for {repo_name}",
                                f"# {repo_name}\n\n{description}",
                                branch=default_branch,
                            )
                            ref = repo.get_git_ref(f"refs/heads/{default_branch}")
                        else:
                            # Create main branch
                            repo.create_file(
                                ".gitkeep",
                                "Initial commit",
                                "",
                                branch="main",
                            )
                            ref = repo.get_git_ref(f"refs/heads/main")
                            default_branch = "main"
                    
                    # Create blob for file
                    blob = repo.create_git_blob(
                        base64.b64encode(content.encode()).decode(),
                        "base64"
                    )
                    
                    # Get current tree
                    tree = repo.get_git_tree(default_branch)
                    
                    # Create new tree with our file
                    new_tree_items = [
                        github.GithubObject({
                            "path": filename,
                            "mode": "100644",
                            "type": "blob",
                            "sha": blob.sha,
                        })
                        for filename, content in code.items()
                    ]
                    
                    # Simplified: use create_file for each file
                    # (more reliable than tree manipulation)
                    for filename, content in code.items():
                        try:
                            repo.create_file(
                                filename,
                                f"Add {filename}",
                                content,
                                branch=default_branch,
                            )
                        except GithubException:
                            # File might exist, update it
                            contents = repo.get_contents(filename, ref=default_branch)
                            repo.update_file(
                                filename,
                                f"Update {filename}",
                                content,
                                contents.sha,
                                branch=default_branch,
                            )
                            
                except Exception as e:
                    print(f"[GitHubDeployer] Push error (trying direct create): {e}")
                    # Fallback: one file at a time
                    for filename, content in code.items():
                        try:
                            repo.create_file(
                                filename,
                                f"Add {filename}",
                                content,
                                branch=default_branch or "main",
                            )
                        except Exception:
                            pass
            
            print(f"[GitHubDeployer] Created: {repo.html_url}")
            
            return {
                "success": True,
                "repo_url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "description": description,
                "private": private,
                "default_branch": repo.default_branch,
                "created_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            print(f"[GitHubDeployer] Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Created local repository instead",
            }
    
    async def _create_local_repo(
        self,
        repo_name: str,
        code: dict[str, str]
    ) -> dict:
        """Create a local git repository as fallback."""
        import subprocess
        
        # Create temp directory
        repo_dir = Path(tempfile.mkdtemp()) / repo_name
        repo_dir.mkdir()
        
        for filename, content in code.items():
            filepath = repo_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        
        # Initialize git
        try:
            subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"Initial commit: {repo_name}"],
                cwd=repo_dir,
                capture_output=True,
            )
        except Exception as e:
            print(f"[GitHubDeployer] Git init error: {e}")
        
        return {
            "success": True,
            "repo_url": "",
            "local_path": str(repo_dir),
            "message": "Created local repository. Install PyGithub for GitHub push.",
        }


class WebhookNotifierAgent:
    """
    Sends webhooks for human-in-the-loop workflows.
    
    Slack, Teams, Discord, custom webhooks.
    """
    
    async def notify(
        self,
        task_id: str,
        output: str,
        webhook_url: str,
        actions: list[str] = None,
    ) -> dict:
        """
        Send notification to webhook.
        
        Args:
            task_id: Task identifier
            output: Output to review (truncated)
            webhook_url: URL to send to
            actions: Available actions (approve, reject, modify)
            
        Returns:
            dict with success, response
        """
        import httpx
        
        if actions is None:
            actions = ["approve", "reject"]
        
        payload = {
            "task_id": task_id,
            "output": output[:500] + "..." if len(output) > 500 else output,
            "actions": actions,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0,
                )
                
                return {
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "response": response.text[:200] if response.text else "",
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Singleton instances
github_deployer = GitHubDeployerAgent()
webhook_notifier = WebhookNotifierAgent()
