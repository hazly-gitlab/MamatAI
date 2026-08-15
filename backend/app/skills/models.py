from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SkillManifest(BaseModel):
    name: str
    version: str
    description: str
    triggers: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    permissions: Dict[str, Any] = Field(default_factory=dict)
    workflow: List[str] = Field(default_factory=list)
    verification: Dict[str, Any] = Field(default_factory=dict)
