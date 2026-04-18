# reviewdog-no-animal-violence

> **Status: Maintenance** — Stable composite GitHub Action. The core pipeline is complete; incremental improvements happen as scanner patterns expand.

A [reviewdog](https://github.com/reviewdog/reviewdog) GitHub Action that detects speciesist language in pull requests and posts **inline review comments** with inclusive alternatives directly on the changed diff lines. Part of the [Open Paws](https://github.com/Open-Paws) no-animal-violence tooling suite.

**Ecosystem:** [no-animal-violence](https://github.com/Open-Paws/no-animal-violence) · [no-animal-violence-action](https://github.com/Open-Paws/no-animal-violence-action) · [no-animal-violence-pre-commit](https://github.com/Open-Paws/no-animal-violence-pre-commit) · [eslint-plugin](https://github.com/Open-Paws/eslint-plugin-no-animal-violence) · [semgrep-rules](https://github.com/Open-Paws/semgrep-rules-no-animal-violence) · [danger-plugin](https://github.com/Open-Paws/danger-plugin-no-animal-violence)

---

## What is reviewdog?

[reviewdog](https://github.com/reviewdog/reviewdog) is a tool that runs any linter or scanner and posts its findings as native GitHub review comments on the exact PR diff lines that triggered them. It consumes output in a standard error format (`file:line: message`) and uses the GitHub API to annotate pull requests — giving contributors immediate, in-context feedback without leaving the code review interface.

This action wraps the `no-animal-violence-pre-commit` scanner in that reviewdog pipeline.

---

## What this action does

1. Installs reviewdog via `reviewdog/action-setup@v1`.
2. Installs the `no-animal-violence-pre-commit` scanner (pip, pinned to v0.2.0).
3. Discovers source files across the repository using `find` (filtered by extension, excluding `.git/`, `node_modules/`, `vendor/`).
4. Pipes scanner output through reviewdog using `-efm="%f:%l: %m"` so each finding maps to a specific file and line.
5. Posts inline PR review comments (or check annotations, depending on `reporter`) with the phrase detected and its suggested inclusive alternative.

The scanner checks for phrases that normalise or trivialise the exploitation of non-human animals and suggests alternatives aligned with animal advocacy movement language.

---

## Quick start

Add the following workflow file to any repository:

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

That is the minimum viable configuration. The action uses sensible defaults for all other inputs.

---

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `github_token` | GitHub token for reviewdog API access | `${{ github.token }}` |
| `level` | Report level: `info`, `warning`, or `error` | `warning` |
| `reporter` | How findings are posted: `github-pr-review` (inline comments), `github-pr-check` (check annotations), or `github-check` | `github-pr-review` |
| `filter_mode` | Which lines to scan — see section below | `added` |

### Reporter comparison

| Reporter | Where findings appear | Requires write permission |
|---|---|---|
| `github-pr-review` | Inline review comments on diff lines | Yes (`pull-requests: write`) |
| `github-pr-check` | Check annotations in the Files tab | Yes (`checks: write`) |
| `github-check` | Check run annotations only | Yes (`checks: write`) |

### Filter modes

| Mode | What is scanned |
|------|-----------------|
| `added` (default) | Only newly added lines in the PR diff |
| `diff_context` | Added lines plus surrounding context lines |
| `file` | Every line in any file that was modified by the PR |
| `nofilter` | Every line in every scanned file in the repository |

Use `added` for incremental adoption — contributors only see feedback on code they wrote in this PR. Switch to `file` or `nofilter` for a full repository audit pass.

---

## Permissions

When using `reporter: github-pr-review`, the workflow token needs explicit write permissions:

```yaml
permissions:
  contents: read
  pull-requests: write

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
          reporter: github-pr-review
```

---

## Supported file types

`.py` · `.js` · `.ts` · `.md` · `.txt` · `.rst` · `.yaml` · `.yml` · `.go` · `.rs` · `.java` · `.rb`

Excluded paths: `.git/`, `node_modules/`, `vendor/`

---

## Example PR annotation output

When a PR adds the line:

```python
# We'll use this repo as a guinea pig for the new deploy process
```

reviewdog posts an inline comment on that line:

```
[no-animal-violence] "guinea pig" used as a verb → use "test subject" instead.
See: https://github.com/Open-Paws/no-animal-violence
```

Other examples of patterns the scanner detects:

| Detected phrase | Suggested alternative |
|---|---|
| `kill two birds with one stone` | `feed two birds with one scone` |
| `beat a dead horse` | `feed a fed horse` |
| `guinea pig` (as verb) | `test subject` |
| `more than one way to skin a cat` | `more than one way to solve this` |
| `cattle` (used as a metaphor for people) | `ephemeral` |

Full pattern list: [no-animal-violence canonical rules](https://github.com/Open-Paws/no-animal-violence)

---

## Relationship to the canonical no-animal-violence rules

All patterns originate from the [no-animal-violence](https://github.com/Open-Paws/no-animal-violence) canonical rule dictionary — the single source of truth for the 65+ patterns the Open Paws suite enforces. The flow is:

```
no-animal-violence (canonical rules)
       |
       └─> no-animal-violence-pre-commit (scanner — regex engine + CLI)
                  |
                  └─> reviewdog-no-animal-violence (this repo)
                             |
                             └─> GitHub PR inline comments via reviewdog
```

This action does not define any patterns itself. It only provides the reviewdog integration layer. When the canonical rules change, updating the scanner version pin in `action.yml` is all that is required.

---

## Comparison with no-animal-violence-action

The Open Paws ecosystem provides two GitHub Actions:

| | `reviewdog-no-animal-violence` (this repo) | `no-animal-violence-action` |
|---|---|---|
| Output style | Inline PR review comments on diff lines | GitHub Check annotations in the Files tab |
| Filter mode | Configurable (`added`, `file`, `nofilter`, …) | Configurable |
| Requires `pull-requests: write` | Yes (for `github-pr-review`) | No |
| Best for | Developer-facing feedback during review | CI gates, status checks |

Teams using Danger.js can use the [danger-plugin-no-animal-violence](https://github.com/Open-Paws/danger-plugin-no-animal-violence) instead.

---

## Contributing

1. Clone the repo and create a feature branch.
2. Edit `action.yml` — this is the entire implementation.
3. Test by opening a PR (in this or another repo that uses this action) containing a known phrase from the [canonical rules](https://github.com/Open-Paws/no-animal-violence). Verify an inline comment appears on the correct line.
4. Run `desloppify scan --path .` — minimum score ≥85.
5. No automated test harness exists yet; real PR testing is the current gate.

Pattern definitions belong in [no-animal-violence](https://github.com/Open-Paws/no-animal-violence), not here. Contributions that add patterns to this repo will be redirected upstream.

---

## License

MIT
