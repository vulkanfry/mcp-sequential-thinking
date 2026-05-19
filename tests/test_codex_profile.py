import unittest

from mcp_sequential_thinking.analysis import ThoughtAnalyzer
from mcp_sequential_thinking.codex_profile import build_codex_guidance
from mcp_sequential_thinking.models import ThoughtData, ThoughtStage


class TestCodexProfile(unittest.TestCase):
    """Tests for Codex-task guidance tailored to this fork."""

    def test_build_codex_guidance_combines_mev_and_github_review_rules(self):
        guidance = build_codex_guidance(
            task_description="Fix GitHub review comments and failing CI for the REVM PR",
            workspace="/Users/vulkanfry/ezilmev/bot+disc/arbitrage",
            tags=["revm", "github", "ci"],
        )

        self.assertIn("github-review-ci", guidance["matchedRules"])
        self.assertIn("mev-rust-runtime", guidance["matchedRules"])
        self.assertIn(
            "Inspect GitHub review comments, threads, or Actions logs directly before guessing.",
            guidance["executionRules"],
        )
        self.assertIn(
            "Trace the runtime path from the diff before editing.", guidance["executionRules"]
        )
        self.assertIn(
            "Run targeted cargo tests plus cargo fmt/clippy when Rust files change.",
            guidance["verificationChecks"],
        )
        self.assertIn("revm", guidance["memoryKeywords"])

    def test_build_codex_guidance_adds_codex_tooling_without_stale_project_rules(self):
        guidance = build_codex_guidance(
            task_description="Improve Codex MCP skill hooks for profile cleanup",
            workspace="/Users/vulkanfry/dev/mcp-sequential-thinking",
            tags=["codex", "mcp", "profile"],
        )

        self.assertEqual(guidance["matchedRules"], ["codex-tooling"])
        self.assertEqual(
            guidance["recommendedTools"],
            ["tool_search", "codex mcp list", "codex debug prompt-input"],
        )
        self.assertIn(
            "Verify live MCP/tool discovery instead of trusting config text.",
            guidance["executionRules"],
        )

    def test_keyword_matching_avoids_substring_false_positives(self):
        guidance = build_codex_guidance(
            task_description="Remove project-specific guidance and run verification before push",
            tags=["metadata"],
        )

        self.assertEqual(guidance["matchedRules"], [])
        self.assertEqual(guidance["recommendedTools"], [])

    def test_build_codex_guidance_keeps_generic_tasks_quiet(self):
        guidance = build_codex_guidance(task_description="Compare two naming options")

        self.assertEqual(guidance["matchedRules"], [])
        self.assertEqual(guidance["executionRules"], [])
        self.assertEqual(guidance["verificationChecks"], [])
        self.assertEqual(guidance["nextActions"], [])
        self.assertEqual(guidance["primaryRule"], None)
        self.assertEqual(guidance["profileDepth"], 0)

    def test_analyze_thought_includes_codex_guidance_when_tags_match(self):
        thought = ThoughtData(
            thought="Plan a CEXDEX REVM fix after GitHub review feedback.",
            thought_number=1,
            total_thoughts=3,
            next_thought_needed=True,
            stage=ThoughtStage.PROBLEM_DEFINITION,
            tags=["cexdex", "revm", "github-review"],
        )

        analysis = ThoughtAnalyzer.analyze_thought(thought, [thought])

        guidance = analysis["thoughtAnalysis"]["codexGuidance"]
        self.assertIn("github-review-ci", guidance["matchedRules"])
        self.assertIn("mev-rust-runtime", guidance["matchedRules"])

    def test_live_run_guidance_requires_waiting_past_cache_catchup(self):
        guidance = build_codex_guidance(
            task_description="Atomic live run is still in cache catch-up during startup",
            workspace="/Users/vulkanfry/ezilmev/bot+disc/arbitrage",
            tags=["atomic", "startup", "cache catch-up"],
        )

        self.assertIn("live-run-readiness", guidance["matchedRules"])
        self.assertEqual(guidance["primaryRule"], "live-run-readiness")
        self.assertIn(
            "Keep watching until the live path actually starts, not just until startup succeeds.",
            guidance["executionRules"],
        )
        self.assertIn(
            "Capture the concrete log line or health signal that proves the live path started.",
            guidance["verificationChecks"],
        )
        self.assertIn(
            "Check startup env/config/token/checkpoint wiring before changing runtime code.",
            guidance["nextActions"],
        )

    def test_staged_diff_guidance_prioritizes_cached_diff_before_search(self):
        guidance = build_codex_guidance(
            task_description="По staged diff посмотри раздувание дифа и лишние helper wrappers",
            workspace="/Users/vulkanfry/ezilmev/bot+disc/arbitrage",
            tags=["staged diff", "review"],
        )

        self.assertIn("staged-diff-review", guidance["matchedRules"])
        self.assertEqual(guidance["primaryRule"], "staged-diff-review")
        self.assertGreaterEqual(guidance["profileDepth"], 2)
        self.assertIn(
            "Inspect the staged patch before broad search or cleanup.",
            guidance["executionRules"],
        )
        self.assertIn(
            "Run git diff --cached --stat and inspect the staged patch first.",
            guidance["nextActions"],
        )

    def test_skill_agent_binding_guidance_requires_runtime_assignment_proof(self):
        guidance = build_codex_guidance(
            task_description="Import local superpowers skills into Multica and bind them to agents",
            tags=["skill import", "agents", "superpowers", "binding"],
        )

        self.assertIn("skill-agent-binding", guidance["matchedRules"])
        self.assertEqual(guidance["primaryRule"], "skill-agent-binding")
        self.assertIn(
            "Verify skills are usable and assigned to agents, not only copied or imported.",
            guidance["executionRules"],
        )
        self.assertIn(
            "Capture created_count, assigned skill counts, or API responses proving binding.",
            guidance["verificationChecks"],
        )

    def test_broad_scan_guidance_routes_to_read_only_subagent(self):
        guidance = build_codex_guidance(
            task_description="Прям глубоко пройдись по всей большой кодовой базе",
            tags=["large codebase scan", "deep scan"],
        )

        self.assertIn("broad-scan-delegation", guidance["matchedRules"])
        self.assertEqual(guidance["primaryRule"], "broad-scan-delegation")
        self.assertIn(
            "For genuinely broad codebase scans, spawn a read-only Codex subagent with model gpt-5.4 and reasoning_effort xhigh.",
            guidance["executionRules"],
        )
        self.assertIn(
            "Define a concrete scan scope before delegation.",
            guidance["nextActions"],
        )

    def test_config_provenance_guidance_demands_exact_env_keys(self):
        guidance = build_codex_guidance(
            task_description="какой env проставить надо и откуда берется mode override",
            workspace="/Users/vulkanfry/ezilmev/bot+disc/arbitrage",
            tags=["env", "config", "override"],
        )

        self.assertIn("config-provenance", guidance["matchedRules"])
        self.assertEqual(guidance["primaryRule"], "config-provenance")
        self.assertIn(
            "Answer with exact env keys, override precedence, and source file paths.",
            guidance["executionRules"],
        )
        self.assertIn(
            "Trace defaults, env parsing, and CLI/config precedence before answering.",
            guidance["nextActions"],
        )


if __name__ == "__main__":
    unittest.main()
