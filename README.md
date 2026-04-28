# Core Hermes - Auto Skill Extractor

Hermes Agentの会話履歴を自動分析し、再利用可能なスキルを抽出するシステム。

## 機能

- **自動パターン検出**: コード生成、デバッグ、分析などのパターンを自動認識
- **SQLite対応**: HermesのセッションDB（`~/.hermes/state.db`）を直接読み込み
- **SKILL.md自動生成**: skill_manage互換のMarkdownスキルファイルを出力
- **重複除去**: 同様のスキルを自動的にマージ

## インストール

```bash
pip install -e .
```

または:

```bash
pip install core-hermes
```

## 使用方法

### CLI

```bash
# 基本的な使い方
python -m auto_skill_extractor --db ~/.hermes/state.db

# オプション指定
python -m auto_skill_extractor \
  --db ~/.hermes/state.db \
  --output ./my_skills \
  --min-confidence 0.8 \
  --max-skills 20

# 直近7日間のみ
python -m auto_skill_extractor --since 7
```

### Python API

```python
from auto_skill_extractor import AutoSkillExtractor, ExtractionConfig

config = ExtractionConfig(
    db_path="~/.hermes/state.db",
    output_dir="./extracted_skills",
    min_confidence=0.7
)

extractor = AutoSkillExtractor(config)
result = extractor.run()

print(f"{result.skills_extracted} skills extracted")
```

## アーキテクチャ

```
auto-skill-extractor/
├── models.py          # Pydanticデータモデル
├── session_reader.py  # SQLite読み込み
├── pattern_analyzer.py # パターン検出
├── skill_extractor.py  # スキル抽出
├── skill_generator.py  # SKILL.md生成
└── main.py            # CLIエントリーポイント
```

## 検出パターン

| パターン | 説明 |
|---------|------|
| CODE_GEN | コード生成・実装支援 |
| DEBUG | エラー解決・デバッグ |
| ANALYSIS | データ分析・調査 |
| SEARCH | 検索・情報抽出 |
| REFACTOR | コード改善・リファクタ |
| INTEGRATION | API連携・サービス統合 |

## テスト済み環境

- macOS / Python 3.9+
- Hermes `state.db` 実データ
- 検証結果: 30セッション / 3932メッセージから29パターン検出、5スキル生成

## 注意

- 生成されたスキルは公開前に人間が内容を確認すること
- 会話内容やツール出力がSKILL.mdに含まれる可能性があるため、秘密情報を含むDBで使う場合は出力確認が必須
- デフォルトDBはHermesの現行スキーマ `~/.hermes/state.db` を想定

## GitHub

https://github.com/gagarot/core-hermes

## License

MIT
