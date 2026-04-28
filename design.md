# auto-skill-extractor 技術設計書

## 概要

Core Hermesプロジェクトの第一弾コンポーネント。Hermes Agentの会話履歴を自動分析し、再利用可能なスキルパターンを検出・抽出するシステム。

---

## 1. アーキテクチャ概要

### 1.1 システム全体図

```
┌─────────────────────────────────────────────────────────────────┐
│                     auto-skill-extractor                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Analyzer   │────▶│  Extractor   │────▶│   Generator  │    │
│  │  (分析層)    │     │  (抽出層)    │     │   (生成層)    │    │
│  └──────┬───────┘     └──────────────┘     └──────┬───────┘    │
│         │                                           │            │
│         ▼                                           ▼            │
│  ┌──────────────┐                           ┌──────────────┐   │
│  │   SQLite     │                           │  SKILL.md    │   │
│  │  (履歴DB)    │                           │   出力       │   │
│  └──────────────┘                           └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 コンポーネント構成

| コンポーネント | 責務 |
|-------------|------|
| **SessionReader** | SQLite履歴DBから会話データ読み込み |
| **PatternAnalyzer** | メッセージパターンの分析・クラスタリング |
| **SkillExtractor** | 再利用可能なスキル候補の抽出 |
| **SkillGenerator** | Markdown形式スキル定義書の生成 |
| **SkillValidator** | 生成スキルの品質検証 |

---

## 2. データフロー

### 2.1 処理フロー図

```
┌────────────────┐
│ Hermes SQLite  │
│ sessions.db    │
│  - messages    │
│  - sessions    │
└───────┬────────┘
        │
        ▼
┌─────────────────────────┐
│ 1. SessionReader        │
│    - DB接続             │
│    - バッチ読み込み      │
│    - メタデータ抽出      │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────┐
│ 2. PatternAnalyzer      │
│    - 類似度計算         │
│    - クラスタリング      │
│    - 頻出パターン検出    │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────┐
│ 3. SkillExtractor       │
│    - パターンマッチング   │
│    - 信頼度スコアリング  │
│    - 重複排除           │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────┐
│ 4. SkillGenerator       │
│    - Markdown生成       │
│    - メタデータ付与     │
│    - テンプレート適用    │
└───────┬─────────────────┘
        │
        ▼
┌────────────────┐
│ SKILL.md 出力  │
└────────────────┘
```

### 2.2 データ変換

```
Raw Messages ──▶ Session Objects ──▶ Pattern Clusters ──▶ Skill Candidates ──▶ Markdown Skills
     │                │                  │                   │                  │
     ▼                ▼                  ▼                   ▼                  ▼
  SQLite rows    Pydantic models    Dict[str, List]    SkillDefinition    File output
```

---

## 3. 主要クラス設計

### 3.1 コアクラス構成

```python
# ========================================
# データモデル層
# ========================================

class SessionMessage(BaseModel):
    """会話メッセージモデル"""
    id: int
    session_id: str
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    timestamp: datetime
    metadata: Optional[dict] = None

class ConversationPattern(BaseModel):
    """検出された会話パターン"""
    pattern_id: str
    pattern_type: PatternType  # CODE, DEBUG, ANALYSIS, etc.
    messages: List[SessionMessage]
    frequency: int
    confidence_score: float  # 0.0 - 1.0
    extracted_at: datetime

class SkillDefinition(BaseModel):
    """抽出されたスキル定義"""
    name: str
    description: str
    triggers: List[str]  # パターンマッチング用
    template: str  # SKILL.mdフォーマット
    examples: List[dict]
    confidence: float
    tags: List[str]

# ========================================
# 分析層クラス
# ========================================

class SessionReader:
    """SQLite履歴DB読み込みクラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> None:
        """データベース接続（FTS5対応）"""
        pass
    
    def get_session_messages(
        self, 
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        batch_size: int = 1000
    ) -> Iterator[List[SessionMessage]]:
        """バッチ単位でメッセージ取得"""
        pass
    
    def search_by_content(
        self, 
        query: str, 
        limit: int = 100
    ) -> List[SessionMessage]:
        """FTS5全文検索"""
        pass

class PatternAnalyzer:
    """パターン分析クラス"""
    
    def __init__(self, config: AnalyzerConfig):
        self.config = config
        self.vectorizer = None  # TF-IDF or similar
    
    def analyze_patterns(
        self, 
        messages: List[SessionMessage]
    ) -> List[ConversationPattern]:
        """メッセージからパターンを分析"""
        pass
    
    def _cluster_similar_messages(
        self, 
        messages: List[SessionMessage]
    ) -> Dict[str, List[SessionMessage]]:
        """類似メッセージをクラスタリング"""
        pass
    
    def _calculate_confidence(
        self, 
        cluster: List[SessionMessage]
    ) -> float:
        """パターンの信頼度計算"""
        pass

class SkillExtractor:
    """スキル抽出クラス"""
    
    def __init__(self, min_confidence: float = 0.7):
        self.min_confidence = min_confidence
    
    def extract_skills(
        self, 
        patterns: List[ConversationPattern]
    ) -> List[SkillDefinition]:
        """パターンからスキル定義を抽出"""
        pass
    
    def _generate_skill_template(
        self, 
        pattern: ConversationPattern
    ) -> str:
        """パターンからスキルテンプレート生成"""
        pass
    
    def _extract_triggers(
        self, 
        messages: List[SessionMessage]
    ) -> List[str]:
        """トリガーフレーズ抽出"""
        pass

class SkillGenerator:
    """SKILL.md生成クラス"""
    
    TEMPLATE = """
# {name}

## Description
{description}

## Triggers
{triggers}

## Examples
{examples}

## Metadata
- Confidence: {confidence}
- Extracted: {extracted_at}
- Tags: {tags}
"""
    
    def generate(self, skill: SkillDefinition) -> str:
        """SKILL.mdフォーマットで出力"""
        pass
    
    def save(self, skill: SkillDefinition, output_dir: str) -> Path:
        """ファイルに保存"""
        pass

# ========================================
# メインコントローラー
# ========================================

class AutoSkillExtractor:
    """メインコントローラークラス"""
    
    def __init__(self, config: ExtractorConfig):
        self.config = config
        self.reader = SessionReader(config.db_path)
        self.analyzer = PatternAnalyzer(config.analyzer_config)
        self.extractor = SkillExtractor(config.min_confidence)
        self.generator = SkillGenerator()
    
    def run(self, output_dir: str) -> ExtractionResult:
        """抽出処理を実行"""
        # 1. データ読み込み
        messages = self._load_messages()
        
        # 2. パターン分析
        patterns = self.analyzer.analyze_patterns(messages)
        
        # 3. スキル抽出
        skills = self.extractor.extract_skills(patterns)
        
        # 4. ファイル生成
        for skill in skills:
            self.generator.save(skill, output_dir)
        
        return ExtractionResult(
            total_messages=len(messages),
            patterns_found=len(patterns),
            skills_extracted=len(skills),
            saved_files=[skill.name for skill in skills]
        )
    
    def run_incremental(
        self, 
        last_run: Optional[datetime] = None
    ) -> ExtractionResult:
        """差分抽出実行"""
        pass
```

---

## 4. スキルパターン分類

### 4.1 自動検出パターン

| パターンタイプ | 説明 | 検出方法 |
|-------------|------|---------|
| **CODE_GEN** | コード生成パターン | コードブロック頻出 + 言語指示 |
| **DEBUG** | デバッグ支援パターン | エラー出力 + 修正提案 |
| **ANALYSIS** | データ分析パターン | 表/グラフ要求 + 複雑な推論 |
| **REFACTOR** | リファクタリング | コード比較 + 改善提案 |
| **SEARCH** | 検索・フィルタリング | FTS操作 + 結果表示 |
| **INTEGRATION** | 外部サービス連携 | API呼び出しパターン |

### 4.2 パターン検出ロジック

```python
class PatternType(str, Enum):
    CODE_GEN = "code_generation"
    DEBUG = "debugging"
    ANALYSIS = "analysis"
    REFACTOR = "refactoring"
    SEARCH = "search"
    INTEGRATION = "integration"
    CUSTOM = "custom"

class PatternDetector:
    """パターン検出ルール"""
    
    RULES = {
        PatternType.CODE_GEN: {
            "patterns": [
                r"```[\w]*\n.*?```",  # コードブロック
                r"(書いて|生成して|作成して)",  # 日本語指示
            ],
            "threshold": 0.8
        },
        PatternType.DEBUG: {
            "patterns": [
                r"(エラー|error|exception|traceback)",
                r"(修正|fix|debug|解決)",
            ],
            "threshold": 0.7
        },
        # ... 他パターン
    }
    
    def detect(self, messages: List[SessionMessage]) -> PatternType:
        # 複合スコアリングで判定
        pass
```

---

## 5. 実装サンプル

### 5.1 最小構成実装

```python
#!/usr/bin/env python3
"""
auto-skill-extractor: 最小構成実装
"""

import sqlite3
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Iterator
from dataclasses import dataclass, asdict

# ----------------------------------------
# データモデル
# ----------------------------------------

@dataclass
class Message:
    id: int
    session_id: str
    role: str
    content: str
    timestamp: str

@dataclass  
class ExtractedSkill:
    name: str
    description: str
    pattern: str
    confidence: float
    extracted_at: str

# ----------------------------------------
# メインクラス
# ----------------------------------------

class SkillExtractor:
    """シンプルなスキル抽出実装"""
    
    # パターンマッチングルール
    PATTERNS = {
        "code_block": r"```[\w]*\n(.+?)```",
        "command": r"(^|\n)\$\s*(.+)",
        "file_path": r"[\/\w]+\.[\w]+",
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.min_confidence = 0.6
    
    def extract(self, output_dir: str = "./skills") -> List[str]:
        """スキル抽出メイン処理"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        skills = []
        
        # データベース読み込み
        messages = self._load_messages()
        print(f"Loaded {len(messages)} messages")
        
        # パターン分析
        patterns = self._analyze_patterns(messages)
        print(f"Found {len(patterns)} patterns")
        
        # スキル生成
        for pattern_name, data in patterns.items():
            if data["confidence"] >= self.min_confidence:
                skill = self._create_skill(pattern_name, data)
                skills.append(skill)
                
                # Markdown保存
                filepath = self._save_skill(skill, output_path)
                print(f"Saved: {filepath}")
        
        return [s.name for s in skills]
    
    def _load_messages(self) -> List[Message]:
        """SQLiteからメッセージ読み込み"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hermes DBスキーマ想定
        cursor.execute("""
            SELECT id, session_id, role, content, timestamp 
            FROM messages 
            ORDER BY timestamp DESC
            LIMIT 1000
        """)
        
        messages = []
        for row in cursor.fetchall():
            messages.append(Message(*row))
        
        conn.close()
        return messages
    
    def _analyze_patterns(self, messages: List[Message]) -> Dict:
        """簡易パターン分析"""
        patterns = {}
        
        # コードブロック検出
        code_blocks = []
        for msg in messages:
            if msg.role == "assistant":
                blocks = re.findall(self.PATTERNS["code_block"], 
                                   msg.content, re.DOTALL)
                code_blocks.extend(blocks)
        
        if code_blocks:
            patterns["code_generation"] = {
                "count": len(code_blocks),
                "confidence": min(1.0, len(code_blocks) / 10),
                "samples": code_blocks[:3],
                "trigger": "code request"
            }
        
        # ファイル操作検出
        file_paths = []
        for msg in messages:
            paths = re.findall(self.PATTERNS["file_path"], msg.content)
            file_paths.extend(paths)
        
        if len(file_paths) > 5:
            patterns["file_operations"] = {
                "count": len(file_paths),
                "confidence": min(1.0, len(file_paths) / 20),
                "samples": list(set(file_paths))[:5],
                "trigger": "file path mention"
            }
        
        return patterns
    
    def _create_skill(self, name: str, data: Dict) -> ExtractedSkill:
        """スキル定義作成"""
        description = f"Auto-extracted {name} pattern ({data['count']} occurrences)"
        
        return ExtractedSkill(
            name=name,
            description=description,
            pattern=data["trigger"],
            confidence=data["confidence"],
            extracted_at=datetime.now().isoformat()
        )
    
    def _save_skill(self, skill: ExtractedSkill, output_dir: Path) -> Path:
        """SKILL.mdとして保存"""
        filename = f"skill_{skill.name}.md"
        filepath = output_dir / filename
        
        content = f"""# {skill.name}

## Description
{skill.description}

## Pattern
`{skill.pattern}`

## Confidence Score
{skill.confidence:.2f}

## Examples
See source conversation history.

## Metadata
- Extracted: {skill.extracted_at}
- Auto-generated: true

## Usage
This skill was automatically extracted from conversation patterns.
Consider manual review before deployment.
"""
        
        filepath.write_text(content, encoding="utf-8")
        return filepath

# ----------------------------------------
# 実行エントリーポイント
# ----------------------------------------

if __name__ == "__main__":
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "./hermes.db"
    
    extractor = SkillExtractor(db_path)
    extracted = extractor.extract()
    
    print(f"\n{'='*40}")
    print(f"Extracted {len(extracted)} skills:")
    for name in extracted:
        print(f"  - {name}")
```

### 5.2 利用例

```bash
# インストール
pip install auto-skill-extractor

# 実行
python -m auto_skill_extractor /path/to/hermes.db --output ./skills

# 設定ファイル指定
python -m auto_skill_extractor --config extractor.yaml
```

---

## 6. データベーススキーマ

### 6.1 SQLiteテーブル設計

```sql
-- メッセージ履歴
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- 全文検索インデックス (FTS5)
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    session_id UNINDEXED,
    content='messages',
    content_rowid='id'
);

-- トリガー: FTS同期
CREATE TRIGGER messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content, session_id)
    VALUES (new.id, new.content, new.session_id);
END;

-- 抽出済みスキル
CREATE TABLE extracted_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    pattern_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_message_ids JSON,
    skill_content TEXT NOT NULL,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_time ON messages(timestamp);
CREATE INDEX idx_skills_confidence ON extracted_skills(confidence);
```

---

## 7. 設定ファイル

### 7.1 YAML設定例

```yaml
# extractor.yaml
extractor:
  db_path: "~/.hermes/sessions.db"
  output_dir: "./skills"
  min_confidence: 0.7
  max_skills: 100
  
analysis:
  batch_size: 1000
  lookback_days: 30
  pattern_types:
    - code_generation
    - debugging
    - analysis
    - search
  
storage:
  format: "markdown"
  include_metadata: true
  
logging:
  level: INFO
  file: "./logs/extractor.log"
```

---

## 8. 今後の拡張

### Phase 1: 基盤 (現在)
- [x] SQLite読み込み
- [x] 基本パターン検出  
- [x] SKILL.md生成

### Phase 2: 強化
- [ ] LLMによるパターン要約
- [ ] セマンティッククラスタリング
- [ ] Web UIダッシュボード

### Phase 3: Core Hermes統合
- [ ] メモリシステム連携
- [ ] スキル自動更新
- [ ] 推論時のスキル推奨

---

## 付録

### A. 依存ライブラリ

```
requirements.txt:
- pydantic>=2.0
- sqlite3 (built-in)
- scikit-learn (clustering)
- click (CLI)
- pyyaml (config)
```

### B. ディレクトリ構造

```
core-hermes/
├── auto-skill-extractor/
│   ├── __init__.py
│   ├── extractor.py      # メインクラス
│   ├── analyzer.py       # 分析ロジック
│   ├── generator.py      # Markdown生成
│   ├── database.py       # DB接続
│   └── cli.py           # コマンドライン
├── config/
│   └── default.yaml
├── tests/
└── README.md
```

---

*設計書作成日: 2026-04-28*
*Core Hermes Project*
