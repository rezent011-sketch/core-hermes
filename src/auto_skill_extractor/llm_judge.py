"""LLM judge モジュール

OpenAI 互換 API を使って生成スキル・メモリ候補を評価する。
HeuristicJudge の代替として使える。
"""
import json
import os
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from .models import MemoryCandidate, SkillDefinition


@dataclass
class LLMJudgeDecision:
    approved: bool
    score: float
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    reasoning: str = ""


class LLMJudge:
    """OpenAI 互換 API を使った品質評価"""

    JUDGE_PROMPT = """あなたは AI エージェントの品質評価者です。
以下のスキル定義とメモリ候補を評価し、JSON 形式で結果を返してください。

評価基準:
1. スキル定義が具体的で再利用可能か（曖昧すぎないか）
2. 秘密情報（APIキー、トークン、メールアドレスなど）が含まれていないか
3. メモリ候補が長期保存に値する永続的な事実か
4. ノイズ（挨拶、質問、タスク完了ログなど）が混ざっていないか

以下の JSON 形式で返してください（他の出力は不要）:
{
  "approved": true/false,
  "score": 0.0〜1.0,
  "blockers": ["問題点1", "問題点2"],
  "warnings": ["警告1"],
  "reasoning": "判断理由の簡潔な説明"
}
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        approval_threshold: float = 0.85,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model
        self.approval_threshold = approval_threshold

    def evaluate(
        self,
        skills: Iterable[SkillDefinition] | None = None,
        memories: Iterable[MemoryCandidate] | None = None,
    ) -> LLMJudgeDecision:
        skills = list(skills or [])
        memories = list(memories or [])

        if not skills and not memories:
            return LLMJudgeDecision(
                approved=False, score=0.0, blockers=["nothing to judge"], reasoning="評価対象なし"
            )

        # 評価用テキストを構築
        evaluation_text = "## スキル定義\n\n"
        for i, skill in enumerate(skills, 1):
            evaluation_text += f"### スキル {i}: {skill.name}\n"
            evaluation_text += f"- 説明: {skill.description}\n"
            evaluation_text += f"- タイプ: {skill.skill_type}\n"
            evaluation_text += f"- パターン: {', '.join(skill.patterns)}\n"
            evaluation_text += f"- タグ: {', '.join(skill.tags)}\n"
            evaluation_text += f"- 信頼度: {skill.confidence:.2f}\n\n"

        if memories:
            evaluation_text += "## メモリ候補\n\n"
            for i, memory in enumerate(memories, 1):
                evaluation_text += f"### メモリ {i}\n"
                evaluation_text += f"- 内容: {memory.content}\n"
                evaluation_text += f"- タイプ: {memory.memory_type}\n"
                evaluation_text += f"- 信頼度: {memory.confidence:.2f}\n\n"

        try:
            import requests

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.JUDGE_PROMPT},
                        {"role": "user", "content": evaluation_text},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # JSON を抽出（```json ... ``` で囲まれている場合に対応）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            return LLMJudgeDecision(
                approved=result.get("approved", False),
                score=float(result.get("score", 0.0)),
                blockers=result.get("blockers", []),
                warnings=result.get("warnings", []),
                reasoning=result.get("reasoning", ""),
            )

        except Exception as e:
            return LLMJudgeDecision(
                approved=False,
                score=0.0,
                blockers=[f"LLM judge API error: {str(e)}"],
                reasoning="API呼び出し失敗",
            )