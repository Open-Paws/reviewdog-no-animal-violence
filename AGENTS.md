# AGENTS.md — reviewdog-no-animal-violence

## Summary

This is a composite GitHub Action that detects speciesist language in pull requests and posts inline review comments via [reviewdog](https://github.com/reviewdog/reviewdog). It chains three tools: the `reviewdog/action-setup` installer, the `no-animal-violence-pre-commit` Python scanner (pip-installed at v0.2.0), and a `find` + pipe invocation that discovers source files, runs the scanner, and routes output through reviewdog's error-format parser (`-efm="%f:%l: %m"`). The entire implementation lives in a single file: `action.yml`. No language runtime beyond bash and Python is required.

---

## Status

**Maintenance** — The core pipeline is stable. Active changes are limited to: scanner version pin bumps, adding supported file extensions, and adjusting excluded directories. The org decision (2026-03-25) mandates this action on all repos. A `fix/correct-repo-name-and-command` branch exists in the remote — evaluate and merge if it addresses a live bug before making other changes.

Implications for agents:
- Safe to update scanner version pin with confirmation.
- Safe to add new file extensions to the `find` command.
- Do not restructure the three-step composite pipeline — it is intentionally minimal.
- Do not add pattern definitions here — those belong in [no-animal-violence](https://github.com/Open-Paws/no-animal-violence).

---

## Key files

| File | Role |
|------|------|
| `action.yml` | The entire implementation — inputs, reviewdog setup, scanner install, find+pipe execution |
| `README.md` | Public-facing docs — usage, inputs, filter modes, examples |
| `CLAUDE.md` | AI agent context, org decisions, architecture notes, development standards |
| `.github/workflows/no-animal-violence.yml` | CI: runs `no-animal-violence-action` on PRs to this repo |
| `.github/workflows/auto-merge.yml` | Auto-merge bot for dependency PRs |
| `.pre-commit-config.yaml` | Pre-commit hook configuration for local development |
| `semgrep-no-animal-violence.yaml` | Semgrep config importing rules from the canonical semgrep-rules repo |

---

## Architecture

```
action.yml (composite)
├── step 1: reviewdog/action-setup@v1          # installs reviewdog binary
├── step 2: pip install no-animal-violence-pre-commit@v0.2.0  # installs scanner CLI
└── step 3: find . -type f ... | no-animal-violence-check ... | reviewdog -efm="%f:%l: %m"
```

The `find` command enumerates files by extension (`*.py`, `*.js`, `*.ts`, `*.md`, `*.txt`, `*.rst`, `*.yaml`, `*.yml`, `*.go`, `*.rs`, `*.java`, `*.rb`) and excludes `.git/`, `node_modules/`, `vendor/`. Scanner output format is `file:line: message`. reviewdog receives this via stdin, maps each finding to a PR diff line using the GitHub API, and posts the result as a review comment (or check annotation depending on `reporter`).

**Four inputs control behaviour:**
- `github_token` — GitHub API token passed to reviewdog via `REVIEWDOG_GITHUB_API_TOKEN`
- `level` — severity to report (`info` / `warning` / `error`)
- `reporter` — output target (`github-pr-review`, `github-pr-check`, `github-check`)
- `filter_mode` — scope (`added`, `diff_context`, `file`, `nofilter`)

---

## Integration points

| Dependency | Version | Purpose |
|---|---|---|
| `reviewdog/action-setup` | v1 | Installs the reviewdog binary |
| `Open-Paws/no-animal-violence-pre-commit` | v0.2.0 (pinned in `action.yml`) | Regex scanner CLI (`no-animal-violence-check`) |
| `actions/checkout` | v4 | Required by callers — not declared internally |
| `actions/setup-python` | v5 | Required by callers — not declared internally |

**MCP integrations (as of 2026-04-11):**
- `mcp-server-nav-language` — Pure-regex MCP server enforcing the same pattern set at agent runtime. reviewdog catches violations in PR diffs; this server catches them in agent-generated content before it reaches a PR.
- `lbr8-mcp-constraints` — Bundles 12 offline NAV patterns as `StaticConstraintSource` middleware.
- `mcp-server-aha-evaluation` — Uses NAV rules as Stage 1 of a two-stage content evaluation pipeline.
- Audit-to-dispatch (decision #37) — NAV violations found in ecosystem audits are now auto-dispatched as agent fix tasks.

---

## How to test

There is no automated test harness. Testing requires a live PR:

1. Add this action to a workflow in any repository.
2. Open a PR that adds a line containing a known phrase (e.g. `# guinea pig for the deploy process`).
3. Confirm an inline review comment appears on that exact line.
4. Vary `reporter` and `filter_mode` inputs to verify different output modes.

Run `desloppify scan --path .` before submitting changes — minimum score ≥85.

---

## Safe vs risky changes

**Safe:**
- Bumping the `no-animal-violence-pre-commit` version pin (test in a live PR first).
- Adding file extensions to the `find` command's extension list.
- Adding directories to the `find` exclusion list.
- Updating `actions/checkout` or `actions/setup-python` version pins.
- README and AGENTS.md edits.

**Risky — requires careful testing:**
- Changing the `reviewdog/action-setup` version.
- Modifying the `-efm` format string — a wrong format silently drops all findings.
- Changing the `find` command structure — malformed commands can silently scan nothing.
- Adding new inputs to `action.yml` — existing callers may need to be updated.

**Do not do:**
- Add pattern definitions here. All patterns live in [no-animal-violence](https://github.com/Open-Paws/no-animal-violence).
- Duplicate scanner logic from `no-animal-violence-pre-commit`.
- Rewrite the three-step composite into a Docker action or JavaScript action without org sign-off.

---

## TODOs

- Evaluate and merge `fix/correct-repo-name-and-command` branch if it addresses a live bug.
- Add this action to `open-paws-platform` CI (see `ecosystem/integration-todos.md` §27a in the context repo).
- Template into new-repo cookiecutter so every new org repo gets inline speciesist language comments on PRs (see §29).
- Assign a named owner — the suite currently has none (noted 2026-04-02).
- Verify whether `Open-Paws/speciesist-language-pre-commit` v0.1.0 (referenced in CLAUDE.md) and `no-animal-violence-pre-commit` v0.2.0 are the same scanner or a divergence that needs documenting.
- Add automated testing via a fixture PR or a test workflow that asserts reviewdog output format.
