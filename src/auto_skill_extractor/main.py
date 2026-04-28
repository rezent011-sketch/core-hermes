"""Core Hermes - auto-skill-extractor メインエントリーポイント

使用例:
    python -m auto_skill_extractor --db ~/.hermes/sessions.db --output ./skills
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

try:
    from .models import ExtractionConfig, ExtractionResult
    from .session_reader import SessionReader
    from .pattern_analyzer import PatternAnalyzer
    from .skill_extractor import SkillExtractor
    from .skill_generator import SkillGenerator
except ImportError:
    from models import ExtractionConfig, ExtractionResult
    from session_reader import SessionReader
    from pattern_analyzer import PatternAnalyzer
    from skill_extractor import SkillExtractor
    from skill_generator import SkillGenerator


class AutoSkillExtractor:
    """自動スキル抽出のメインコントローラー"""
    
    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.reader = SessionReader(config.db_path)
        self.extractor = SkillExtractor(config.min_confidence)
        self.generator = SkillGenerator(config.output_dir)
    
    def run(self, since: Optional[datetime] = None) -> ExtractionResult:
        """抽出処理を実行"""
        print(f"🚀 Core Hermes - Auto Skill Extractor")
        print(f"   DB: {self.config.db_path}")
        print(f"   Output: {self.config.output_dir}")
        print(f"   Min confidence: {self.config.min_confidence}")
        print()
        
        with self.reader:
            # セッション一覧を取得
            sessions = self.reader.get_recent_sessions(limit=100)
            print(f"📊 {len(sessions)} sessions found")
            
            # 各セッションを処理
            all_skills = []
            total_messages = 0
            
            for session in sessions:
                session_id = session["session_id"]
                messages = list(self.reader.get_messages_for_session(session_id, since))
                
                if not messages:
                    continue
                
                total_messages += len(messages)
                
                # スキルを抽出
                skill = self.extractor.extract_from_session(messages, session_id)
                if skill:
                    all_skills.append(skill)
            
            # 重複除去・フィルタリング
            unique_skills = self._deduplicate_skills(all_skills)
            unique_skills = unique_skills[:self.config.max_skills_per_run]
            
            print(f"🔍 {len(unique_skills)} unique skills detected")
            
            # スキルを保存
            saved_files = []
            for skill in unique_skills:
                filepath = self.generator.generate(skill, self.config.output_dir)
                saved_files.append(str(filepath))
                print(f"   ✓ {skill.name} ({skill.confidence:.2f})")
            
            result = ExtractionResult(
                total_messages=total_messages,
                patterns_found=len(all_skills),
                skills_extracted=len(unique_skills),
                saved_files=saved_files
            )
            
            print(f"\n✅ Extraction complete!")
            print(f"   {result.skills_extracted} skills saved to {self.config.output_dir}")
            
            return result
    
    def _deduplicate_skills(self, skills: list) -> list:
        """重複スキルを除去"""
        seen = set()
        unique = []
        for skill in skills:
            if skill.name not in seen:
                unique.append(skill)
                seen.add(skill.name)
        return unique


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Core Hermes - Auto Skill Extractor"
    )
    parser.add_argument(
        "--db", "-d",
        type=Path,
        default=Path("~/.hermes/sessions.db"),
        help="SQLite database path"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./extracted_skills"),
        help="Output directory for skills"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold (0.0-1.0)"
    )
    parser.add_argument(
        "--max-skills",
        type=int,
        default=10,
        help="Maximum skills to extract per run"
    )
    parser.add_argument(
        "--since",
        type=int,
        default=None,
        help="Extract from N days ago"
    )
    
    args = parser.parse_args()
    
    config = ExtractionConfig(
        db_path=args.db,
        output_dir=args.output,
        min_confidence=args.min_confidence,
        max_skills_per_run=args.max_skills
    )
    
    since = None
    if args.since:
        since = datetime.now() - timedelta(days=args.since)
    
    extractor = AutoSkillExtractor(config)
    result = extractor.run(since)
    
    # 結果サマリーをJSONで出力
    import json
    print("\n" + "=" * 50)
    print(json.dumps(result.model_dump(), indent=2, default=str))
    
    return 0 if result.skills_extracted > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
