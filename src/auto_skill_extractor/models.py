"""Core Hermes - auto-skill-extractor データモデル"""
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SkillType(str, Enum):
    """スキルパターンタイプ"""
    CODE_GEN = "code_generation"
    DEBUG = "debugging"
    ANALYSIS = "analysis"
    REFACTOR = "refactoring"
    SEARCH = "search"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class MemoryType(str, Enum):
    """長期メモリ候補タイプ"""
    USER_PREFERENCE = "user_preference"
    ENVIRONMENT = "environment"
    PROJECT_FACT = "project_fact"
    WORKFLOW = "workflow"


class OrchestratorAction(str, Enum):
    """次に実行すべき安全な改善アクション"""
    EXTRACT_SKILLS = "extract_skills"
    REVIEW_MEMORIES = "review_memories"
    ENHANCE_CONTEXT = "enhance_context"
    IDLE = "idle"


class SessionMessage(BaseModel):
    """セッションメッセージ"""
    id: str
    role: str  # "user", "assistant", "tool", "system"
    content: str
    timestamp: datetime
    session_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryCandidate(BaseModel):
    """会話履歴から抽出した保存候補メモリ"""
    content: str
    memory_type: MemoryType
    confidence: float
    evidence_session_id: str
    source_message_id: str
    tags: List[str] = Field(default_factory=list)


class ContextEnhancement(BaseModel):
    """次セッションへ注入できる安全な文脈"""
    summary: str
    relevant_memories: List[MemoryCandidate] = Field(default_factory=list)
    relevant_skills: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class OrchestratorDecision(BaseModel):
    """Core Hermes v2.0 オーケストレーター判断"""
    action: OrchestratorAction
    reason: str
    confidence: float
    next_steps: List[str] = Field(default_factory=list)


class SkillDefinition(BaseModel):
    """抽出されたスキル定義"""
    name: str
    description: str
    skill_type: SkillType
    patterns: List[str]  # 検出パターン
    example_conversation: List[SessionMessage]
    confidence: float  # 0.0-1.0
    created_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    
    def to_skill_md(self) -> str:
        """SKILL.md形式で出力"""
        return f"""---
name: {self.name}
description: "{self.description}"
version: 1.0.0
tags: [{', '.join(f'"{t}"' for t in self.tags)}]
---

# {self.name}

{self.description}

## 検出パターン

- {chr(10).join('- ' + p for p in self.patterns)}

## 例示会話

{self._format_examples()}

## 使用方法

このスキルタイプ: `{self.skill_type}`
"""
    
    def _format_examples(self) -> str:
        """例示会話をMarkdown形式で整形"""
        lines = []
        for msg in self.example_conversation[:5]:  # 最大5件
            role_ja = {"user": "ユーザー", "assistant": "アシスタント"}.get(msg.role, msg.role)
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            lines.append(f"**{role_ja}**: {content}")
        return "\n\n".join(lines)


class ExtractionConfig(BaseModel):
    """抽出設定"""
    db_path: Path = Path("~/.hermes/sessions.db").expanduser()
    output_dir: Path = Path("./extracted_skills")
    min_confidence: float = 0.7
    max_skills_per_run: int = 10
    min_pattern_occurrence: int = 3  # 最少出現回数
    dry_run: bool = False
    review: bool = False
    install: bool = False
    memory_review: bool = False
    context_query: Optional[str] = None
    orchestrate: bool = False
    report_path: Optional[Path] = None
    manifest_path: Optional[Path] = None
    strict: bool = False
    memory_review_path: Optional[Path] = None
    unsafe_no_sanitize: bool = False
    judge: bool = False
    quality_threshold: float = 0.85
    safe_auto: bool = False
    auto_threshold: float = 0.93
    review_threshold: float = 0.75
    hermes_home: Optional[Path] = None


class ExtractionResult(BaseModel):
    """抽出結果"""
    total_messages: int
    patterns_found: int
    skills_extracted: int
    saved_files: List[str]
    errors: List[str] = Field(default_factory=list)
    memory_candidates: List[MemoryCandidate] = Field(default_factory=list)
    context_enhancement: Optional[ContextEnhancement] = None
    orchestrator_decision: Optional[OrchestratorDecision] = None
    exit_code: Optional[int] = None
    judge_score: Optional[float] = None
    quality_gate_passed: Optional[bool] = None


