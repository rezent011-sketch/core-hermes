"""Core Hermes - auto-skill-extractor パッケージ"""

__version__ = "1.0.0"

from .models import (
    SessionMessage,
    SkillDefinition,
    SkillType,
    ExtractionConfig,
    ExtractionResult,
)
from .session_reader import SessionReader
from .pattern_analyzer import PatternAnalyzer
from .skill_extractor import SkillExtractor
from .skill_generator import SkillGenerator
from .main import AutoSkillExtractor

__all__ = [
    "SessionMessage",
    "SkillDefinition",
    "SkillType",
    "ExtractionConfig",
    "ExtractionResult",
    "SessionReader",
    "PatternAnalyzer",
    "SkillExtractor",
    "SkillGenerator",
    "AutoSkillExtractor",
]
