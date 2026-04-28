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
    from .quality import SkillDeduplicator, SkillValidator
    from .installer import SkillInstaller
    from .smart_memory import SmartMemoryExtractor
    from .context_enhancer import ContextEnhancer
    from .orchestrator import CoreHermesOrchestrator
except ImportError:
    from models import ExtractionConfig, ExtractionResult
    from session_reader import SessionReader
    from pattern_analyzer import PatternAnalyzer
    from skill_extractor import SkillExtractor
    from skill_generator import SkillGenerator
    from quality import SkillDeduplicator, SkillValidator
    from installer import SkillInstaller
    from smart_memory import SmartMemoryExtractor
    from context_enhancer import ContextEnhancer
    from orchestrator import CoreHermesOrchestrator


class AutoSkillExtractor:
    """自動スキル抽出のメインコントローラー"""
    
    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.reader = SessionReader(config.db_path)
        self.extractor = SkillExtractor(config.min_confidence)
        self.generator = SkillGenerator(config.output_dir)
        self.deduplicator = SkillDeduplicator()
        self.validator = SkillValidator()
        self.memory_extractor = SmartMemoryExtractor()
        self.context_enhancer = ContextEnhancer()
        self.orchestrator = CoreHermesOrchestrator()
    
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
            all_messages = []
            
            for session in sessions:
                session_id = session["session_id"]
                messages = list(self.reader.get_messages_for_session(session_id, since))
                
                if not messages:
                    continue
                
                total_messages += len(messages)
                all_messages.extend(messages)
                
                # スキルを抽出
                skill = self.extractor.extract_from_session(messages, session_id)
                if skill:
                    all_skills.append(skill)
            
            # 重複統合・品質検証
            unique_skills = self.deduplicator.deduplicate(all_skills)
            validated_skills = []
            errors = []
            for skill in unique_skills:
                validation = self.validator.validate(skill)
                if validation.is_valid:
                    validated_skills.append(skill)
                else:
                    errors.extend([f"{skill.name}: {e}" for e in validation.errors])
            unique_skills = validated_skills[:self.config.max_skills_per_run]
            
            print(f"🔍 {len(unique_skills)} quality skills detected")
            
            # スキルを保存（dry-run時は書き込まない）
            saved_files = []
            target_output = self.config.output_dir / "review" if self.config.review else self.config.output_dir
            for skill in unique_skills:
                if self.config.dry_run:
                    print(f"   DRY-RUN ✓ {skill.name} ({skill.confidence:.2f})")
                    continue
                filepath = self.generator.generate(skill, target_output)
                saved_files.append(str(filepath))
                print(f"   ✓ {skill.name} ({skill.confidence:.2f})")
            
            memory_candidates = self.memory_extractor.extract(all_messages) if self.config.memory_review else []
            context_enhancement = None
            if self.config.context_query:
                context_enhancement = self.context_enhancer.enhance(
                    self.config.context_query,
                    memory_candidates,
                    self.config.output_dir,
                )

            result = ExtractionResult(
                total_messages=total_messages,
                patterns_found=len(all_skills),
                skills_extracted=len(unique_skills),
                saved_files=saved_files,
                errors=errors,
                memory_candidates=memory_candidates,
                context_enhancement=context_enhancement,
            )
            if self.config.orchestrate:
                result.orchestrator_decision = self.orchestrator.decide(result, self.config.output_dir, reviewed=self.config.review)
            
            if memory_candidates:
                print(f"   {len(memory_candidates)} memory candidates ready for review")
            if context_enhancement:
                print(f"   Context: {context_enhancement.summary[:160]}")
            if result.orchestrator_decision:
                print(f"   Orchestrator: {result.orchestrator_decision.action} - {result.orchestrator_decision.reason}")

            if self.config.install and saved_files:
                installer = SkillInstaller()
                installed = [installer.install_file(Path(p)) for p in saved_files]
                saved_files.extend(str(p) for p in installed)
                print(f"   {len(installed)} skills installed to Hermes")

            print(f"\n✅ Extraction complete!")
            print(f"   {result.skills_extracted} skills saved to {target_output if not self.config.dry_run else 'dry-run'}")
            
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
    parser.add_argument("--dry-run", action="store_true", help="Analyze only; do not write files")
    parser.add_argument("--review", action="store_true", help="Write skills under output/review for manual review")
    parser.add_argument("--install", action="store_true", help="Install reviewed/generated skills into ~/.hermes/skills/core-hermes")
    parser.add_argument("--memory-review", action="store_true", help="Generate smart-memory candidates for manual review")
    parser.add_argument("--context-query", type=str, default=None, help="Build task-specific context from memory and generated skills")
    parser.add_argument("--orchestrate", action="store_true", help="Ask Core Hermes orchestrator for next safe action")
    parser.add_argument("--install-from", type=Path, default=None, help="Install .md skills from a directory and exit")
    parser.add_argument("--hermes-home", type=Path, default=Path("~/.hermes"), help="Hermes home directory")
    
    args = parser.parse_args()

    if args.install_from:
        installed = SkillInstaller(args.hermes_home).install_directory(args.install_from)
        print(f"✅ Installed {len(installed)} skills")
        for path in installed:
            print(f"   ✓ {path}")
        return 0
    
    config = ExtractionConfig(
        db_path=args.db,
        output_dir=args.output,
        min_confidence=args.min_confidence,
        max_skills_per_run=args.max_skills,
        dry_run=args.dry_run,
        review=args.review,
        install=args.install,
        memory_review=args.memory_review,
        context_query=args.context_query,
        orchestrate=args.orchestrate
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

