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
    from .reporter import ReportWriter
    from .manifest import ManifestWriter
    from .safety import SafetyAuditor
    from .memory_review import MemoryReviewWriter
    from .judge import HeuristicJudge
    from .quality_gate import QualityGate
    from .safe_auto import SafeAutoRunner, SafeAutoPolicy
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
    from reporter import ReportWriter
    from manifest import ManifestWriter
    from safety import SafetyAuditor
    from memory_review import MemoryReviewWriter
    from judge import HeuristicJudge
    from quality_gate import QualityGate
    from safe_auto import SafeAutoRunner, SafeAutoPolicy


class AutoSkillExtractor:
    """自動スキル抽出のメインコントローラー"""
    
    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.reader = SessionReader(config.db_path)
        self.extractor = SkillExtractor(config.min_confidence)
        self.generator = SkillGenerator(config.output_dir)
        if config.unsafe_no_sanitize:
            self.generator.sanitizer.sanitize = lambda text: text or ""
        self.deduplicator = SkillDeduplicator()
        self.validator = SkillValidator()
        self.memory_extractor = SmartMemoryExtractor()
        self.context_enhancer = ContextEnhancer()
        self.orchestrator = CoreHermesOrchestrator()
        self.reporter = ReportWriter()
        self.manifest_writer = ManifestWriter()
        self.safety_auditor = SafetyAuditor()
        self.memory_review_writer = MemoryReviewWriter()
        self.judge = HeuristicJudge(config.quality_threshold)
        self.quality_gate = QualityGate(config.quality_threshold)
    
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
            
            # 各セッションを処理（並列化）
            all_skills = []
            total_messages = 0
            all_messages = []
            
            # セッションデータ事前読み込み
            session_data = []
            for session in sessions:
                session_id = session["session_id"]
                messages = list(self.reader.get_messages_for_session(session_id, since))
                if messages:
                    session_data.append((messages, session_id))
                    total_messages += len(messages)
                    all_messages.extend(messages)
            
            print(f"   Processing {len(session_data)} sessions with {total_messages} messages...")
            
            # 並列抽出（CPU バウンドではないので ThreadPool で十分）
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def extract_skill(args):
                messages, session_id = args
                return self.extractor.extract_from_session(messages, session_id)
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(extract_skill, data): data for data in session_data}
                for future in as_completed(futures):
                    skill = future.result()
                    if skill:
                        all_skills.append(skill)
            
            print(f"   Extracted {len(all_skills)} raw skills")
            
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
            
            judge_decision = None
            if self.config.judge:
                judge_decision = self.judge.evaluate(unique_skills, memory_candidates)
                result.judge_score = judge_decision.score
                print(f"   Judge: {judge_decision.score:.2f} approved={judge_decision.approved}")

            gate_result = None
            if self.config.strict:
                gate_result = self.quality_gate.check(result, judge_decision)
                result.quality_gate_passed = gate_result.passed
                if not gate_result.passed:
                    result.errors.extend(gate_result.reasons)
                    print("Quality gate failed")

            if memory_candidates:
                print(f"   {len(memory_candidates)} memory candidates ready for review")
            if context_enhancement:
                print(f"   Context: {context_enhancement.summary[:160]}")
            if result.orchestrator_decision:
                print(f"   Orchestrator: {result.orchestrator_decision.action} - {result.orchestrator_decision.reason}")

            if saved_files:
                audit = self.safety_auditor.audit_files(Path(p) for p in saved_files)
                if not audit.is_safe:
                    result.errors.extend([f"safety audit failed: {f.kind}" for f in audit.findings[:10]])

            if getattr(self.config, "memory_review_path", None):
                memory_review_path = self.memory_review_writer.write(memory_candidates, self.config.memory_review_path)
                print(f"   Memory review written: {memory_review_path}")
            if getattr(self.config, "manifest_path", None):
                manifest_path = self.manifest_writer.write(result, self.config.manifest_path)
                print(f"   Manifest written: {manifest_path}")
            if getattr(self.config, "report_path", None):
                report_path = self.reporter.write(result, self.config.report_path)
                print(f"   Report written: {report_path}")

            if self.config.strict and (result.errors or result.skills_extracted == 0 or result.quality_gate_passed is False):
                print("Strict mode failed")
                result.exit_code = 2

            if self.config.safe_auto:
                safe_runner = SafeAutoRunner(
                    output_dir=self.config.output_dir,
                    hermes_home=getattr(self.config, "hermes_home", Path("~/.hermes")),
                    policy=SafeAutoPolicy(self.config.auto_threshold, self.config.review_threshold),
                )
                safe_decisions = safe_runner.run(unique_skills, result.judge_score or 0.0)
                print(f"   Safe-auto: {sum(d.action == 'auto_install' for d in safe_decisions)} auto, {sum(d.action == 'review' for d in safe_decisions)} review, {sum(d.action == 'reject' for d in safe_decisions)} reject")

            if self.config.install and saved_files and not result.errors:
                installer = SkillInstaller()
                installed = [installer.install_file(Path(p)) for p in saved_files]
                saved_files.extend(str(p) for p in installed)
                print(f"   {len(installed)} skills installed to Hermes")

            print(f"\n✅ Extraction complete!")
            print(f"   {result.skills_extracted} skills saved to {target_output if not self.config.dry_run else 'dry-run'}")
            
            # 増分モード：最終実行時刻を記録
            if self.config.incremental and not self.config.dry_run:
                marker = self.config.output_dir / ".last_run"
                marker.write_text(str(datetime.now().timestamp()))
            
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
    parser.add_argument("--report", type=Path, default=None, help="Write a safe markdown summary report")
    parser.add_argument("--manifest", type=Path, default=None, help="Write a machine-readable safe manifest")
    parser.add_argument("--strict", action="store_true", help="Exit 2 if no skills or any validation/safety error")
    parser.add_argument("--memory-review-out", type=Path, default=None, help="Write memory candidates to a checkbox review markdown")
    parser.add_argument("--unsafe-no-sanitize", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--judge", action="store_true", help="Run heuristic judge compatible with future LLM judge")
    parser.add_argument("--quality-threshold", type=float, default=0.85, help="Minimum judge score for strict quality gate")
    parser.add_argument("--safe-auto", action="store_true", help="Safely auto-install only high-confidence zero-risk skills; quarantine the rest")
    parser.add_argument("--auto-threshold", type=float, default=0.93, help="Safe-auto threshold for automatic install")
    parser.add_argument("--review-threshold", type=float, default=0.75, help="Safe-auto threshold for review quarantine")
    parser.add_argument("--install-from", type=Path, default=None, help="Install .md skills from a directory and exit")
    parser.add_argument("--hermes-home", type=Path, default=Path.home() / ".hermes", help="Hermes home directory")
    parser.add_argument("--incremental", action="store_true", help="Incremental mode: only process sessions since last extraction")
    
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
        orchestrate=args.orchestrate,
        report_path=args.report,
        manifest_path=args.manifest,
        strict=args.strict,
        memory_review_path=args.memory_review_out,
        unsafe_no_sanitize=args.unsafe_no_sanitize,
        judge=args.judge,
        quality_threshold=args.quality_threshold,
        safe_auto=args.safe_auto,
        auto_threshold=args.auto_threshold,
        review_threshold=args.review_threshold,
        hermes_home=args.hermes_home,
        incremental=args.incremental
    )
    
    since = None
    if args.since:
        since = datetime.now() - timedelta(days=args.since)
    
    # 増分モード：前回の抽出以降のみ処理
    if config.incremental:
        last_run_marker = args.output_dir / ".last_run"
        if last_run_marker.exists():
            last_run = float(last_run_marker.read_text().strip())
            since = datetime.fromtimestamp(last_run)
            print(f"   Incremental mode: processing sessions since {since}")
        else:
            print("   Incremental mode: no previous run found, processing all sessions")
    
    if config.safe_auto:
        config.judge = True
    extractor = AutoSkillExtractor(config)
    result = extractor.run(since)
    
    # 結果サマリーをJSONで出力
    import json
    print("\n" + "=" * 50)
    print(json.dumps(result.model_dump(), indent=2, default=str))
    
    if getattr(result, "exit_code", None) is not None:
        return result.exit_code
    return 0 if result.skills_extracted > 0 else 1


if __name__ == "__main__":
    sys.exit(main())






