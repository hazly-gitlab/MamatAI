import os
import shutil
import tempfile
import subprocess
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("jarvis_sandbox")

class Sandbox:
    def __init__(self, sandbox_dir: Optional[str] = None):
        self._temp_dir_obj = None
        if not sandbox_dir:
            self._temp_dir_obj = tempfile.TemporaryDirectory(prefix="jarvis_sandbox_")
            self.path = self._temp_dir_obj.name
        else:
            self.path = sandbox_dir
            os.makedirs(self.path, exist_ok=True)
        logger.info(f"Initialized sandbox environment at: {self.path}")

    def copy_file_into(self, src_filepath: str, dest_relative_path: str):
        """Copies a production file into the sandbox safely."""
        if not os.path.exists(src_filepath):
            raise FileNotFoundError(f"Source file {src_filepath} does not exist.")

        dest_path = os.path.join(self.path, dest_relative_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_filepath, dest_path)
        logger.info(f"Copied {src_filepath} into sandbox at {dest_relative_path}")

    def copy_dir_into(self, src_dirpath: str, dest_relative_path: str):
        """Copies a directory tree into the sandbox safely."""
        if not os.path.exists(src_dirpath):
            raise FileNotFoundError(f"Source directory {src_dirpath} does not exist.")

        dest_path = os.path.join(self.path, dest_relative_path)
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.copytree(src_dirpath, dest_path)
        logger.info(f"Copied directory {src_dirpath} into sandbox at {dest_relative_path}")

    def apply_patch(self, relative_filepath: str, search_block: str, replace_block: str) -> bool:
        """Applies simple search-and-replace style code patches within the sandbox."""
        full_path = os.path.join(self.path, relative_filepath)
        if not os.path.exists(full_path):
            logger.error(f"Cannot patch: file {relative_filepath} not found in sandbox.")
            return False

        with open(full_path, "r") as f:
            content = f.read()

        if search_block not in content:
            logger.error(f"Cannot patch: search block not found in {relative_filepath}")
            return False

        new_content = content.replace(search_block, replace_block)
        with open(full_path, "w") as f:
            f.write(new_content)

        logger.info(f"Successfully applied patch to sandboxed {relative_filepath}")
        return True

    def run_command(self, cmd_args: List[str], timeout: float = 10.0, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Runs a command inside the sandbox context cleanly."""
        # Sanitize command to prevent dangerous execution
        restricted_binaries = ["rm", "sh", "bash", "curl", "wget", "nc", "sudo"]
        if cmd_args and cmd_args[0] in restricted_binaries:
            return {
                "status": "failed",
                "exit_code": -1,
                "stdout": "",
                "stderr": "Access Denied: Restricted binary execution in sandbox."
            }

        # Setup isolated environment variables
        sandbox_env = {
            "PYTHONPATH": f"{self.path}:{os.path.join(self.path, 'backend')}",
            "PATH": os.environ.get("PATH", "")
        }
        if env:
            sandbox_env.update(env)

        try:
            res = subprocess.run(
                cmd_args,
                cwd=self.path,
                capture_output=True,
                text=True,
                env=sandbox_env,
                timeout=timeout
            )
            return {
                "status": "success" if res.returncode == 0 else "failed",
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr
            }
        except subprocess.TimeoutExpired as te:
            return {
                "status": "timeout",
                "exit_code": -1,
                "stdout": te.stdout or "",
                "stderr": "Execution exceeded timeout limit."
            }
        except Exception as e:
            return {
                "status": "failed",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }

    def cleanup(self):
        """Cleans up temporary directory after use."""
        if self._temp_dir_obj:
            try:
                self._temp_dir_obj.cleanup()
                logger.info("Cleaned up sandbox temporary files.")
            except Exception as e:
                logger.error(f"Error cleaning sandbox: {str(e)}")
