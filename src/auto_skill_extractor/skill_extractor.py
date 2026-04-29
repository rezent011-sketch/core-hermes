"""スキル抽出モジュール"""
from datetime import datetime
from typing import List, Optional

from .models import (
    SessionMessage,
    SkillDefinition,
    SkillType,
    ExtractionConfig
)
from .pattern_analyzer import PatternAnalyzer


class SkillExtractor:
    """検出されたパターンからスキル定義を生成"""
    
    def __init__(self, min_confidence: float = 0.7):
        self.min_confidence = min_confidence
        self.analyzer = PatternAnalyzer(min_confidence)
    
    def extract_from_session(
        self,
        messages: List[SessionMessage],
        session_id: str
    ) -> Optional[SkillDefinition]:
        """単一セッションからスキルを抽出"""
        if len(messages) < 2:  # 最小長チェック
            return None
        
        # パターン分析
        scores = self.analyzer.analyze_session(messages)
        
        if not scores:
            return None
        
        # 最高スコアのパターンを選択
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]
        
        if confidence < self.min_confidence:
            return None
        
        # スキル定義を生成
        return self._create_skill_definition(
            messages=messages,
            skill_type=best_type,
            confidence=confidence,
            session_id=session_id
        )
    
    def extract_from_multiple_sessions(
        self,
        sessions: List[List[SessionMessage]]
    ) -> List[SkillDefinition]:
        """複数セッションからスキルを抽出（重複除去付き）"""
        skills = []
        seen_patterns = set()
        
        for messages in sessions:
            if not messages:
                continue
                
            session_id = messages[0].session_id
            skill = self.extract_from_session(messages, session_id)
            
            if skill and skill.name not in seen_patterns:
                skills.append(skill)
                seen_patterns.add(skill.name)
        
        # 信頼度でソート
        skills.sort(key=lambda s: s.confidence, reverse=True)
        
        return skills
    
    def _create_skill_definition(
        self,
        messages: List[SessionMessage],
        skill_type: SkillType,
        confidence: float,
        session_id: str
    ) -> SkillDefinition:
        """スキル定義を作成"""
        # キーワード抽出
        keywords = self.analyzer.extract_keywords(messages)
        
        # スキル名を生成
        name = self._generate_name(skill_type, keywords)
        
        # 説明文を生成
        description = self._generate_description(messages, skill_type)
        
        # パターンを特定
        patterns = self._extract_patterns(messages, skill_type)
        
        return SkillDefinition(
            name=name,
            description=description,
            skill_type=skill_type,
            patterns=patterns,
            example_conversation=messages[:5],  # 最初の5メッセージ
            confidence=confidence,
            tags=keywords[:5],  # 上位5キーワード
            prerequisites=[]
        )
    
    def _generate_name(self, skill_type: SkillType, keywords: List[str]) -> str:
        """スキル名を生成"""
        type_names = {
            SkillType.CODE_GEN: "code-generation",
            SkillType.DEBUG: "debugging",
            SkillType.ANALYSIS: "data-analysis",
            SkillType.SEARCH: "search-filter",
            SkillType.REFACTOR: "refactoring",
            SkillType.INTEGRATION: "api-integration",
            SkillType.CUSTOM: "custom-pattern"
        }
        
        base_name = type_names.get(skill_type, "unknown")
        
        # キーワードがあれば追加
        if keywords:
            keyword_part = "-".join(keywords[:2])
            return f"{base_name}-{keyword_part}"
        
        # タイムスタンプでユニーク化
        import uuid
        return f"{base_name}-{uuid.uuid4().hex[:8]}"
    
    def _generate_description(
        self,
        messages: List[SessionMessage],
        skill_type: SkillType
    ) -> str:
        """説明文を生成"""
        type_descriptions = {
            SkillType.CODE_GEN: "コード生成と実装支援",
            SkillType.DEBUG: "エラー解決とデバッグ支援",
            SkillType.ANALYSIS: "データ分析と調査",
            SkillType.SEARCH: "検索と情報抽出",
            SkillType.REFACTOR: "コード改善とリファクタリング",
            SkillType.INTEGRATION: "外部サービス連携",
            SkillType.CUSTOM: "カスタムパターン"
        }
        
        base = type_descriptions.get(skill_type, "汎用パターン")
        
        # 最初のユーザーメッセージから意図を推測
        user_messages = [m for m in messages if m.role == "user"]
        if user_messages:
            first_intent = user_messages[0].content[:50] + "..."
            return f"{base}: {first_intent}"
        
        return base
    
    def _extract_patterns(
        self,
        messages: List[SessionMessage],
        skill_type: SkillType
    ) -> List[str]:
        """パターンを抽出"""
        patterns = []
        
        # ユーザーメッセージからパターンを抽出
        user_contents = [m.content for m in messages if m.role == "user"]
        
        for content in user_contents[:3]:  # 最初の3件
            # 質問パターンを抽出
            if "?" in content or "？" in content:
                patterns.append(content.split("?")[0] + "?")
            # 命令パターンを抽出
            elif len(content) < 100:
                patterns.append(content[:80])
        
        # スキルタイプ別追加パターン
        type_patterns = {
            SkillType.CODE_GEN: ["コードを書いて", "実装して", "```で生成"],
            SkillType.DEBUG: ["エラー修正", "トラブルシュート", "動かない"],
            SkillType.ANALYSIS: ["分析して", "調査して", "比較して"],
            SkillType.SEARCH: ["検索", "探して", "where is"],
            SkillType.REFACTOR: ["リファクタ", "改善", "整理"],
            SkillType.INTEGRATION: ["連携", "API", "統合"]
        }
        
        if skill_type in type_patterns:
            patterns.extend(type_patterns[skill_type])
        
        return patterns[:5]  # 最大5個
