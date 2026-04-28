---
name: debugging-Traceback
description: "エラー解決とデバッグ支援: Python CLIでTracebackが出る。原因を調べて修正して..."
version: 1.0.0
tags: ["Traceback"]
metadata:
  skill_type: SkillType.DEBUG
  confidence: 0.80
  created_at: 2026-04-28T23:55:43.003311
---

# debugging-Traceback

エラー解決とデバッグ支援: Python CLIでTracebackが出る。原因を調べて修正して...

## 検出パターン

- Python CLIでTracebackが出る。原因を調べて修正して
- エラー修正
- トラブルシュート
- 動かない

## 例示会話

### 👤 User

Python CLIでTracebackが出る。原因を調べて修正して

---

### 🤖 Assistant

エラーを再現し、入力検証の不足を確認します

---

### 🔧 Tool

Traceback: ValueError: invalid input

---

### 🤖 Assistant

入力検証を追加し、テストで回帰を防ぎます


## 使用ガイド

### 前提条件

- Hermes Agent環境
- Python 3.10+

### 適用シナリオ

- エラートラブルシュート\n- ログ分析

### 関連機能

- `debugging` タイプのスキル
- タグ: Traceback

---

*自動生成されたスキル定義（Core Hermes auto-skill-extractor）*
