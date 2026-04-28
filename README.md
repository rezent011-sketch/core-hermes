# Core Hermes - Auto Skill Extractor

Hermes Agentの `~/.hermes/state.db` を分析し、過去会話から再利用可能な `SKILL.md` 候補・メモリ候補・次回文脈を生成するCore Hermes実験実装。

## 機能

- **auto-skill-extractor**: コード生成、デバッグ、分析、検索などの会話パターンを検出
- **安全マスク**: APIキー、トークン、Telegram ID、メールなどを出力前にマスク
- **品質管理**: スコアリング、重複統合、SKILL.md事前検証
- **review/install CLI**: `--dry-run` / `--review` / `--install-from` / `--install`
- **smart-memory**: 長期記憶に保存する価値がある候補をレビュー用に抽出
- **context-enhancer**: タスクに関連するメモリ・スキルを短い文脈に圧縮
- **orchestrator**: 次に取るべき安全なアクションを判断

## インストール

```bash
git clone https://github.com/rezent011-sketch/core-hermes.git
cd core-hermes
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

## 使用方法

```bash
# まずは解析だけ（ファイルを書かない）
core-hermes-extract --db ~/.hermes/state.db --dry-run

# レビュー用ディレクトリに出力
core-hermes-extract --db ~/.hermes/state.db --output ./extracted_skills --review

# smart-memory / context-enhancer / orchestrator も実行
core-hermes-extract \
  --db ~/.hermes/state.db \
  --output ./extracted_skills \
  --memory-review \
  --context-query "Hermes skills GitHub" \
  --orchestrate

# レビュー済みスキルをHermesへ導入
core-hermes-extract --install-from ./extracted_skills/review --hermes-home ~/.hermes
```

## 安全方針

- 生成物は必ず人間レビュー前提
- `--install` / `--install-from` は既存ファイルをバックアップしてから導入
- `test_state.db` や生成済みスキルはGit管理しない
- 秘密情報はマスクするが、公開前の目視確認は必須

## アーキテクチャ

```text
auto_skill_extractor/
├── session_reader.py      # Hermes state.db読み込み
├── pattern_analyzer.py    # 会話パターン検出
├── skill_extractor.py     # スキル候補生成
├── skill_generator.py     # SKILL.md生成 + サニタイズ
├── quality.py             # スコアリング・重複統合・検証
├── installer.py           # Hermes skills安全導入
├── smart_memory.py        # メモリ候補抽出
├── context_enhancer.py    # 関連文脈生成
├── orchestrator.py        # 次アクション判断
└── main.py                # CLI
```

## 検証済み

- macOS / Python 3.12
- Hermes `state.db` 実データ
- 30 sessions / 3932 messages
- 29 patterns → 5 quality skills
- テスト: 15 passed

## GitHub

https://github.com/rezent011-sketch/core-hermes

## License

MIT
