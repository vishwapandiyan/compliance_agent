"""Tool for cloning GitHub repositories."""

import os
import tempfile
import git
from typing import Optional
from langchain.tools import tool
from scanner.utils import get_directory_size, format_size

MAX_REPO_SIZE = 1024 * 1024 * 1024  # 1GB in bytes


@tool
def clone_repository(repo_url: str, github_token: Optional[str] = None) -> str:
    """
    Clone a GitHub repository to a temporary directory.
    
    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
        github_token: Optional GitHub personal access token for private repos
        
    Returns:
        Path to the cloned repository directory
        
    Raises:
        Exception: If cloning fails or repository exceeds size limit
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix='devguard_')
    
    try:
        # Modify URL if token is provided
        if github_token:
            # Convert https://github.com/user/repo to https://token@github.com/user/repo
            if repo_url.startswith('https://github.com/'):
                repo_url_with_token = repo_url.replace(
                    'https://github.com/',
                    f'https://{github_token}@github.com/'
                )
            else:
                repo_url_with_token = repo_url
        else:
            repo_url_with_token = repo_url
        
        # Clone the repository
        repo = git.Repo.clone_from(repo_url_with_token, temp_dir)
        
        # Check repository size
        repo_size = get_directory_size(temp_dir)
        if repo_size > MAX_REPO_SIZE:
            # Cleanup and raise error
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(
                f"Repository size ({format_size(repo_size)}) exceeds maximum allowed size "
                f"({format_size(MAX_REPO_SIZE)}). Please use a smaller repository."
            )
        
        return temp_dir
        
    except git.exc.GitCommandError as e:
        # Cleanup on error
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(f"Failed to clone repository: {str(e)}")
    except Exception as e:
        # Cleanup on error
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(f"Error cloning repository: {str(e)}")


