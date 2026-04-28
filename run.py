#!/usr/bin/env python3
"""実行ラッパー - PYTHONPATH設定済み"""
import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# メイン実行
from auto_skill_extractor.main import main
sys.exit(main())
