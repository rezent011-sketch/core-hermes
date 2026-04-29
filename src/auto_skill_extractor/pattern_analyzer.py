"""パターン分析モジュール"""
import re
from collections import Counter
from typing import Dict, List, Tuple

from .models import SessionMessage, SkillType


class PatternAnalyzer:
    """メッセージからパターンを検出・分析"""
    
    # 検出ルール
    PATTERNS = {
        SkillType.CODE_GEN: {
            "regex": [
                r"```[a-zA-Z0-9]*\n[\s\S]{0,5000}?```",  # コードブロック（5000 文字制限）
                r"(?:書いて | 作成して | 生成して | 実装して)",
                r"(?:python|javascript|typescript|rust|go|bash|shell)",
            ],
            "threshold": 0.6,
            "min_count": 2
        },
        SkillType.DEBUG: {
            "regex": [
                r"(?:エラー|error|exception|traceback|bug)",
                r"(?:修正|fix|debug|解決|トラブルシュート)",
                r"(?:失敗|fail|not working|doesn't work)",
            ],
            "threshold": 0.5,
            "min_count": 2
        },
        SkillType.ANALYSIS: {
            "regex": [
                r"(?:分析|analyze|調査|調べて)",
                r"(?:比較|compare|評価|evaluate)",
                r"(?:データ|data|表|グラフ|chart)",
            ],
            "threshold": 0.5,
            "min_count": 2
        },
        SkillType.SEARCH: {
            "regex": [
                r"(?:検索|search|探して|find|look for)",
                r"(?:ファイル|file|grep|where is)",
            ],
            "threshold": 0.5,
            "min_count": 2
        },
        SkillType.REFACTOR: {
            "regex": [
                r"(?:リファクタ|refactor|改善|最適化|optimize)",
                r"(?:整理|clean up|コードの整理)",
            ],
            "threshold": 0.5,
            "min_count": 2
        },
        SkillType.INTEGRATION: {
            "regex": [
                r"(?:API|連携|統合|integrate|接続)",
                r"(?:サービス|service|webhook|callback)",
            ],
            "threshold": 0.5,
            "min_count": 2
        },
    }
    
    def __init__(self, min_confidence: float = 0.7):
        self.min_confidence = min_confidence
    
    def analyze_session(self, messages: List[SessionMessage]) -> Dict[SkillType, float]:
        """セッションを分析してパターンスコアを返す"""
        if not messages:
            return {}
        
        # 全メッセージのコンテンツを結合
        all_content = "\n".join(m.content for m in messages)
        
        scores = {}
        for skill_type, rules in self.PATTERNS.items():
            score = self._calculate_score(all_content, messages, rules)
            if score >= self.min_confidence:
                scores[skill_type] = score
        
        return scores
    
    def _calculate_score(
        self,
        content: str,
        messages: List[SessionMessage],
        rules: dict
    ) -> float:
        """マッチスコアを計算"""
        matches = 0
        total_patterns = len(rules["regex"])
        
        for pattern in rules["regex"]:
            if re.search(pattern, content, re.IGNORECASE):
                matches += 1
        
        # 基本スコア
        base_score = matches / total_patterns if total_patterns > 0 else 0
        
        # 出現回数ボーナス
        message_count = len(messages)
        occurrence_bonus = min(message_count / rules.get("min_count", 3), 1.0)
        
        # 重み付け
        final_score = (base_score * 0.6) + (occurrence_bonus * 0.4)
        
        return min(final_score, 1.0)
    
    def extract_keywords(self, messages: List[SessionMessage]) -> List[str]:
        """キーワードを抽出"""
        all_text = " ".join(m.content for m in messages)
        
        # コードブロックを除去
        text = re.sub(r"```[\s\S]*?```", "", all_text)
        
        # 日本語・英語の単語を抽出
        words = re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}|[a-zA-Z_][a-zA-Z0-9_]{2,}", text)
        
        # 頻出単語を返す
        counter = Counter(words)
        return [word for word, count in counter.most_common(10) if count >= 2]
