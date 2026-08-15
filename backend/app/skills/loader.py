import os
import yaml
import logging
from typing import Dict, Any, List
from app.skills.models import SkillManifest

logger = logging.getLogger("jarvis_skills")

def load_manifest_from_file(filepath: str) -> Dict[str, Any]:
    """Loads a single YAML manifest file."""
    try:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
            return data
    except Exception as e:
        logger.error(f"Error loading manifest from {filepath}: {str(e)}")
        raise e

def load_all_manifests(directory: str) -> List[Dict[str, Any]]:
    """Loads all yaml manifest files from directory."""
    manifests = []
    if not os.path.exists(directory):
        logger.warning(f"Manifests directory {directory} does not exist.")
        return []

    for filename in os.listdir(directory):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            filepath = os.path.join(directory, filename)
            try:
                data = load_manifest_from_file(filepath)
                manifests.append(data)
            except Exception:
                continue
    return manifests
