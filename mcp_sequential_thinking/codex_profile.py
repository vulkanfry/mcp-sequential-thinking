import re
from typing import Any, Dict, List

_RULES = [
    {
        "id": "github-review-ci",
        "priority": 60,
        "keywords": [
            "github",
            "pull request",
            " pr ",
            "review",
            "comment",
            "thread",
            "ci",
            "actions",
            "linter",
            "gh ",
        ],
        "recommendedTools": ["GitHub connector", "gh cli", "git"],
        "executionRules": [
            "Inspect GitHub review comments, threads, or Actions logs directly before guessing.",
            "Treat review-thread state as part of the task, not just the local diff.",
        ],
        "verificationChecks": [
            "Re-check PR thread or check status after the fix is pushed.",
        ],
        "nextActions": [
            "Fetch review comments, unresolved threads, or Actions logs before editing.",
        ],
        "memoryKeywords": ["github review", "gh api", "actions logs", "pull request"],
        "riskFlags": ["Stale local diffs can hide unresolved remote review state."],
    },
    {
        "id": "mev-rust-runtime",
        "priority": 50,
        "keywords": [
            "revm",
            "cexdex",
            "mev",
            "arbitrage",
            "discovery",
            "liquidator",
            "blink",
            "univ4",
            "curve",
            "rust",
            "cargo",
            "atomic",
            "/ezilmev/",
            "bot+disc",
        ],
        "recommendedTools": ["rg", "cargo test", "cargo clippy", "cargo fmt"],
        "executionRules": [
            "Trace the runtime path from the diff before editing.",
            "Keep hot-path changes small, explicit, and evidence-backed.",
            "Do not replace runtime evidence with contract-only or source-only guesses.",
        ],
        "verificationChecks": [
            "Run targeted cargo tests plus cargo fmt/clippy when Rust files change.",
            "Capture concrete non-zero amounts, logs, or diagnostics when behavior is runtime-sensitive.",
        ],
        "nextActions": [
            "Search the concrete runtime path and identify the narrowest file/function to change.",
        ],
        "memoryKeywords": ["revm", "cexdex", "arbitrage", "blink", "cargo clippy"],
        "riskFlags": ["Latency-sensitive paths can regress without obvious compile failures."],
    },
    {
        "id": "live-run-readiness",
        "priority": 100,
        "keywords": [
            "live run",
            "live-run",
            "startup",
            "cache catch-up",
            "cache catchup",
            "bootstrap",
            "readiness",
            "sync",
            "checkpoint",
            "token bootstrap",
            "started",
        ],
        "recommendedTools": ["logs", "process status", "config inspection"],
        "executionRules": [
            "Keep watching until the live path actually starts, not just until startup succeeds.",
            "Check startup env/config/token/checkpoint wiring before changing runtime code.",
        ],
        "verificationChecks": [
            "Capture the concrete log line or health signal that proves the live path started.",
        ],
        "nextActions": [
            "Check startup env/config/token/checkpoint wiring before changing runtime code.",
            "Watch the post-cache-catch-up logs until the live loop emits its first real activity.",
        ],
        "memoryKeywords": ["cache catch-up", "startup", "checkpoint", "live path"],
        "riskFlags": [
            "Startup success can be a false positive while cache catch-up is still running."
        ],
    },
    {
        "id": "staged-diff-review",
        "priority": 100,
        "keywords": [
            "staged diff",
            "git diff --cached",
            "cached diff",
            "staged patch",
            "по staged diff",
            "раздувание дифа",
            "лишние helper",
            "dead wrapper",
            "dead wrappers",
        ],
        "recommendedTools": ["git diff --cached", "git diff --cached --stat", "rg"],
        "executionRules": [
            "Inspect the staged patch before broad search or cleanup.",
            "Anchor review and docs updates to the actual staged change surface.",
        ],
        "verificationChecks": [
            "Re-run staged diff/stat after cleanup to prove the intended scope changed.",
        ],
        "nextActions": [
            "Run git diff --cached --stat and inspect the staged patch first.",
            "Search for single-use helpers, dead wrappers, and unrelated test noise only after reading the staged patch.",
        ],
        "memoryKeywords": ["staged diff", "dead wrappers", "git diff --cached"],
        "riskFlags": ["Broad searching first can drift into code not touched by the current diff."],
    },
    {
        "id": "codex-tooling",
        "priority": 40,
        "keywords": [
            "codex",
            "mcp",
            "skill",
            "skills",
            "hook",
            "hooks",
            "agents.md",
            "config.toml",
            "developer_instructions",
            "tool_search",
        ],
        "recommendedTools": ["tool_search", "codex mcp list", "codex debug prompt-input"],
        "executionRules": [
            "Verify live MCP/tool discovery instead of trusting config text.",
            "Keep instruction changes durable across AGENTS.md, config, and relevant skills.",
            "Avoid noisy high-frequency hooks unless they add visible value.",
        ],
        "verificationChecks": [
            "Run the smallest live discovery or prompt-input check that proves the surface changed.",
        ],
        "nextActions": [
            "Run codex mcp list or tool_search before relying on a configured surface.",
        ],
        "memoryKeywords": ["codex hooks", "skill routing", "mcp list", "config.toml"],
        "riskFlags": ["Current sessions can cache stale hook and MCP registrations."],
    },
    {
        "id": "remote-ops",
        "priority": 80,
        "keywords": [
            "ssh",
            "systemd",
            "remote",
            "host",
            "node",
            "service",
            "restart",
            "journalctl",
            "docker",
        ],
        "recommendedTools": ["ssh", "systemctl", "journalctl", "docker/compose"],
        "executionRules": [
            "Make the smallest targeted live-host change and verify service state on the host.",
            "Never print private keys, tokens, or secret env values.",
        ],
        "verificationChecks": [
            "Report concrete live status, peer count, IPC output, or service logs.",
        ],
        "nextActions": [
            "Verify current host/service state before editing remote files.",
        ],
        "memoryKeywords": ["ssh", "systemd", "remote host", "service status"],
        "riskFlags": ["A copied config is not proof that auth or service state works."],
    },
    {
        "id": "docs-artifacts",
        "priority": 70,
        "keywords": [
            "docs",
            "documentation",
            "architecture",
            "architecture.md",
            "readme",
            "prd",
            "spec",
        ],
        "recommendedTools": ["filesystem", "rg"],
        "executionRules": [
            "Update the named artifact in place when it already exists.",
            "Ground docs in the actual change surface and commands, not generic prose.",
        ],
        "verificationChecks": [
            "Re-read the changed artifact and verify links, paths, and commands are concrete.",
        ],
        "nextActions": [
            "Locate the existing artifact and inspect the relevant code surface before writing docs.",
        ],
        "memoryKeywords": ["docs", "architecture", "README"],
        "riskFlags": ["Large docs can drift from runtime behavior unless checked against code."],
    },
    {
        "id": "skill-agent-binding",
        "priority": 100,
        "keywords": [
            "skill import",
            "skills import",
            "bind skills",
            "skill binding",
            "assigned skills",
            "agent binding",
            "multica",
            "superpowers skills",
            "agents",
        ],
        "recommendedTools": [
            "skill validator",
            "API response inspection",
            "codex debug prompt-input",
        ],
        "executionRules": [
            "Verify skills are usable and assigned to agents, not only copied or imported.",
            "Use the canonical install/import path when one exists instead of hand-copying partial skill state.",
        ],
        "verificationChecks": [
            "Capture created_count, assigned skill counts, or API responses proving binding.",
        ],
        "nextActions": [
            "Inspect the target skill/agent registry and identify the canonical create/update endpoint.",
            "Verify the resulting skill is both present and bound to the intended agent or routing surface.",
        ],
        "memoryKeywords": ["skill import", "agent binding", "superpowers skills", "Multica"],
        "riskFlags": ["A copied skill folder is not proof that routing or agent assignment works."],
    },
    {
        "id": "broad-scan-delegation",
        "priority": 100,
        "keywords": [
            "large codebase scan",
            "broad scan",
            "deep scan",
            "всей большой кодовой базе",
            "прям глубоко",
            "глубоко пройдись",
            "поглубже покопаешь",
        ],
        "recommendedTools": ["spawn_agent", "rg", "code-review-graph"],
        "executionRules": [
            "For genuinely broad codebase scans, spawn a read-only Codex subagent with model gpt-5.4 and reasoning_effort xhigh.",
            "Wait for the subagent conclusion before relying on broad-scan findings.",
        ],
        "verificationChecks": [
            "Compare the subagent findings against the concrete files or diffs before editing.",
        ],
        "nextActions": [
            "Define a concrete scan scope before delegation.",
            "Keep local work focused on non-overlapping evidence while the scan runs.",
        ],
        "memoryKeywords": ["large codebase scan", "gpt-5.4", "read-only subagent"],
        "riskFlags": [
            "Broad scans done inline can miss important context due to context-window pressure."
        ],
    },
    {
        "id": "config-provenance",
        "priority": 100,
        "keywords": [
            "env",
            "environment variable",
            "какой env",
            "config value",
            "override",
            "mode precedence",
            "откуда берется",
            "проставить надо",
            "defaults",
        ],
        "recommendedTools": ["rg", "config file inspection", "runtime command help"],
        "executionRules": [
            "Answer with exact env keys, override precedence, and source file paths.",
            "Verify config defaults before recommending a value.",
        ],
        "verificationChecks": [
            "Show the exact config/env source and the command or test that proves precedence.",
        ],
        "nextActions": [
            "Trace defaults, env parsing, and CLI/config precedence before answering.",
        ],
        "memoryKeywords": ["env key", "override", "config defaults", "mode precedence"],
        "riskFlags": [
            "Guessing env names causes runtime drift that looks like business logic failure."
        ],
    },
]


def _extend_unique(target: List[str], values: List[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _matches_rule(search_text: str, keywords: List[str]) -> bool:
    for keyword in keywords:
        needle = keyword.casefold().strip()
        if not needle:
            continue

        if "/" in needle or "+" in needle:
            if needle in search_text:
                return True
            continue

        pattern = rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])"
        if re.search(pattern, search_text):
            return True

    return False


def build_codex_guidance(
    task_description: str = "",
    workspace: str = "",
    task_kind: str = "",
    tags: List[str] | None = None,
    constraints: List[str] | None = None,
) -> Dict[str, Any]:
    """Build Codex workflow guidance from task text, workspace, and tags.

    The rules are intentionally local and pragmatic. They encode repeated task
    patterns from this user's memory without requiring the MCP server to read
    private memory files directly.
    """
    tags = tags or []
    constraints = constraints or []
    search_text = " ".join([task_description, workspace, task_kind, *tags, *constraints]).casefold()

    guidance: Dict[str, Any] = {
        "matchedRules": [],
        "recommendedTools": [],
        "executionRules": [],
        "verificationChecks": [],
        "nextActions": [],
        "memoryKeywords": [],
        "riskFlags": [],
        "primaryRule": None,
        "profileDepth": 0,
    }

    matched_rules = [rule for rule in _RULES if _matches_rule(search_text, rule["keywords"])]
    matched_rules.sort(key=lambda rule: rule.get("priority", 0), reverse=True)

    for rule in matched_rules:
        if guidance["primaryRule"] is None:
            guidance["primaryRule"] = rule["id"]
        guidance["matchedRules"].append(rule["id"])
        _extend_unique(guidance["recommendedTools"], rule["recommendedTools"])
        _extend_unique(guidance["executionRules"], rule["executionRules"])
        _extend_unique(guidance["verificationChecks"], rule["verificationChecks"])
        _extend_unique(guidance["nextActions"], rule["nextActions"])
        _extend_unique(guidance["memoryKeywords"], rule["memoryKeywords"])
        _extend_unique(guidance["riskFlags"], rule["riskFlags"])

    guidance["profileDepth"] = len(guidance["matchedRules"])
    return guidance
