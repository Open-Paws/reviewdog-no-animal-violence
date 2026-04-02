# Reviewdog No Animal Violence

A [reviewdog](https://github.com/reviewdog/reviewdog) GitHub Action that detects speciesist language in pull requests and posts inline review comments with inclusive alternatives. Part of the [No Animal Violence](https://github.com/Open-Paws) speciesist language detection suite for Open Paws.

## Quick Start

```yaml
# .github/workflows/speciesism.yml
name: Speciesist Language Check
on: [pull_request]

jobs:
  speciesism:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - uses: Open-Paws/reviewdog-no-animal-violence@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Architecture

This is a **composite GitHub Action** that chains three tools:

1. **reviewdog** (installed via `reviewdog/action-setup@v1`) -- posts findings as inline PR comments
2. **speciesist-language-pre-commit** (pip-installed from `Open-Paws/speciesist-language-pre-commit`) -- the actual scanner with regex-based pattern matching
3. **find + pipe** -- discovers source files by extension, excludes `.git/`, `node_modules/`, `vendor/`, pipes scanner output through reviewdog's error format parser (`-efm="%f:%l: %m"`)

**Filter modes** control scope: `added` (new lines only, default), `diff_context`, `file`, or `nofilter` (entire repo).

## Key Files

| File | Description |
|------|-------------|
| `action.yml` | Composite action -- inputs, reviewdog setup, scanner install, find+pipe execution |
| `README.md` | Usage docs, inputs table, filter mode explanation, supported file types |
| `LICENSE` | MIT license |

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `github_token` | `${{ github.token }}` | GitHub token for reviewdog API access |
| `level` | `warning` | Report level: `info`, `warning`, `error` |
| `reporter` | `github-pr-review` | reviewdog reporter type |
| `filter_mode` | `added` | Scope filter: `added`, `diff_context`, `file`, `nofilter` |

## Dependencies

- Requires Python 3.x (via `actions/setup-python`)
- Depends on [Open-Paws/speciesist-language-pre-commit](https://github.com/Open-Paws/speciesist-language-pre-commit) v0.1.0 for the scanner
- Depends on [reviewdog/action-setup](https://github.com/reviewdog/action-setup) for the review posting engine

## Organizational Context

**Strategic role (Lever 1 + Lever 3):** GitHub Action that posts inline PR review comments via reviewdog — the most developer-visible CI integration in the suite. Unlike `no-animal-violence-action` (check annotations), this action posts comments directly on the diff lines where phrases appear.

**Note:** Depends on `Open-Paws/speciesist-language-pre-commit` v0.1.0 — different name from `no-animal-violence-pre-commit` v0.2.0. Verify these are the same scanner or document the divergence.

**Current org priorities relevant to this repo:**
- Should be added to `open-paws-platform` CI. See `ecosystem/integration-todos.md` §27a.
- Template into new-repo cookiecutter so every new org repo gets inline speciesist language comments on PRs. See §29.
- Suite maintenance has **no named owner** as of 2026-04-02.
- `fix/correct-repo-name-and-command` branch exists in remote — evaluate and merge if it fixes an active bug.

**Decisions affecting this repo:**
- 2026-03-25: Every org repo must run speciesist language checks on PRs. This action provides the most developer-friendly presentation.

## Related Repos

- [no-animal-violence](https://github.com/Open-Paws/no-animal-violence) — Canonical rule dictionary
- [no-animal-violence-action](https://github.com/Open-Paws/no-animal-violence-action) — Alternative GitHub Action (check annotations)
- [no-animal-violence-pre-commit](https://github.com/Open-Paws/no-animal-violence-pre-commit) — Local git hook (complements this action)
- [danger-plugin-no-animal-violence](https://github.com/Open-Paws/danger-plugin-no-animal-violence) — Danger.js alternative for teams using Danger

## Development Standards

### 10-Point Review Checklist (ranked by AI violation frequency)

1. **DRY** — Scanner logic lives in `speciesist-language-pre-commit`. Don't duplicate scanner code here; call the installed scanner.
2. **Deep modules** — Three components chained: reviewdog setup, scanner install, find+pipe. Each is a clear step.
3. **Single responsibility** — File discovery, scanning, and annotation posting are three distinct steps.
4. **Error handling** — If the scanner returns non-zero but reviewdog can't parse the output, the action must fail loudly, not silently succeed.
5. **Information hiding** — Users see four inputs (github_token, level, reporter, filter_mode). Internal find+pipe logic is an implementation detail.
6. **Ubiquitous language** — "farmed animal" not "livestock," "factory farm" not "farm." Never introduce synonyms.
7. **Design for change** — Scanner version pin must be updated deliberately. Any version change requires testing.
8. **Legacy velocity** — Before modifying find+pipe logic, test against a real PR with known phrases.
9. **Over-patterning** — Composite action chaining three tools is the right architecture.
10. **Test quality** — Test against a real PR containing known phrases. Verify inline comments appear at the correct diff lines.

### Quality Gates

- **Test in a real repo**: Open a PR with known phrases, add the action, verify inline comments appear.
- **Desloppify**: `desloppify scan --path .` — minimum score ≥85.
- **Two-failure rule**: After two failed fixes on the same problem, stop and restart.

### Seven Concerns — Repo-Specific Notes

1. **Testing** — Manual testing against real PRs. No automated test harness.
2. **Security** — Requires `github.token` with PR write access for posting review comments. Verify minimum required permissions.
3. **Privacy** — Scans PR diff content in CI. No retention beyond the CI run.
4. **Cost optimization** — Composite action. Python install adds startup time — acceptable.
5. **Advocacy domain** — Scanner messages must use movement-standard language.
6. **Accessibility** — Inline PR comments must be clear and actionable.
7. **Emotional safety** — Comments explain the alternative without graphic detail.

### Structured Coding Reference

For tool-specific AI coding instructions (Claude Code rules, Cursor MDC, Copilot, Windsurf, etc.), copy the corresponding directory from `structured-coding-with-ai` into this project root.
