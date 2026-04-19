# reviewdog-no-animal-violence

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Speciesist%20Language%20Scanner-blue?logo=github)](https://github.com/marketplace/actions/speciesist-language-scanner-reviewdog)
[![Status: Maintenance](https://img.shields.io/badge/Status-Maintenance-yellow.svg)](https://github.com/Open-Paws/reviewdog-no-animal-violence)
[![Open Paws](https://img.shields.io/badge/Open%20Paws-nonprofit-brightgreen.svg)](https://openpaws.ai)

Reviewdog runner for animal violence language detection in PRs. This composite GitHub Action embeds a self-contained Python scanner in a [reviewdog](https://github.com/reviewdog/reviewdog) pipeline to post **inline review comments** with inclusive alternatives directly on the changed diff lines of pull requests. It detects speciesist phrases — language that normalises the exploitation of non-human animals — and surfaces them to contributors at review time, in context, without leaving the GitHub interface.

> [!NOTE]
> This project is part of the [Open Paws](https://openpaws.ai) ecosystem — AI infrastructure for the animal liberation movement. [Explore the full platform →](https://github.com/Open-Paws)

---

## Visual

When a PR adds a line containing a detected phrase, reviewdog posts an inline comment on that exact diff line:

```
# PR diff line:
- config["workers"] = get_cattle_pool()  # scale cattle vs. pets dynamically
+ config["workers"] = get_cattle_pool()  # scale ephemeral vs. persistent dynamically

# Reviewdog inline comment on the diff line:
[no-animal-violence] "cattle vs. pets" — Infrastructure metaphor that treats animals as objects — technically imprecise alternatives exist. Consider: "ephemeral vs. persistent", "disposable vs. unique", "numbered vs. named"
```

Other examples posted as inline comments:

| Detected phrase | Why it is flagged | Suggested alternatives |
|---|---|---|
| `kill two birds with one stone` | Violent animal idiom with universally clearer alternatives. | `accomplish two things at once`, `solve two problems with one action` |
| `beat a dead horse` | Violent animal idiom — alternatives are more direct. | `belabor the point`, `go over old ground` |
| `guinea pig` (used as a verb) | Uses an animal-as-experiment metaphor. | `test subject`, `early adopter` |
| `more than one way to skin a cat` | Violent animal idiom — alternatives are shorter and clearer. | `more than one way to solve this` |
| `cattle vs. pets` | Infrastructure metaphor that treats animals as objects. | `ephemeral vs. persistent` |

Full pattern list: [no-animal-violence canonical rules](https://github.com/Open-Paws/no-animal-violence)

---

## Quickstart

1. Create `.github/workflows/speciesism.yml` in your repository.
2. Paste the workflow below.
3. Open a pull request — the action runs automatically on `pull_request` events.
4. Inline review comments appear on any diff lines containing detected phrases.
5. Adjust `filter_mode` to `file` or `nofilter` for a full repository audit pass.

```yaml
# .github/workflows/speciesism.yml
name: Speciesist Language Check
on: [pull_request]

permissions:
  contents: read
  pull-requests: write

jobs:
  speciesism:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Open-Paws/reviewdog-no-animal-violence@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

Note: `actions/setup-python` is no longer required — the action uses the Python 3 runtime already present on all GitHub-hosted runners.

That is the minimum viable configuration. All other inputs use sensible defaults.

---

## Features

### What it checks

All patterns are embedded directly in `scan.py` inside this repository — 70+ phrases that normalise or trivialise the exploitation of non-human animals. The scanner checks `.py`, `.js`, `.ts`, `.md`, `.txt`, `.rst`, `.yaml`, `.yml`, `.go`, `.rs`, `.java`, and `.rb` files.

Excluded paths: `.git/`, `node_modules/`, `vendor/`

### PR annotation format

Each finding is posted as a native GitHub review comment on the exact diff line that triggered it, using the format:

```
[no-animal-violence] "<phrase>" — <reason>. Consider: "<alt1>", "<alt2>"
```

This gives reviewers the full picture — what was detected, why it is flagged, and what to use instead — in one inline comment.

### Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `github_token` | GitHub token for reviewdog API access | `${{ github.token }}` |
| `level` | Report level: `info`, `warning`, or `error` | `warning` |
| `reporter` | `github-pr-review` (inline comments), `github-pr-check` (check annotations), or `github-check` | `github-pr-review` |
| `filter_mode` | Which lines to scan — `added`, `diff_context`, `file`, or `nofilter` | `added` |

**Filter modes:**

| Mode | What is scanned |
|------|----------------|
| `added` (default) | Only newly added lines in the PR diff |
| `diff_context` | Added lines plus surrounding context lines |
| `file` | Every line in any file modified by the PR |
| `nofilter` | Every line in every scanned file in the repository |

Use `added` for incremental adoption — contributors only see feedback on lines they wrote. Switch to `file` or `nofilter` for a full repository audit.

### Comparison with no-animal-violence-action

| | `reviewdog-no-animal-violence` (this repo) | `no-animal-violence-action` |
|---|---|---|
| Output style | Inline PR review comments on diff lines | GitHub Check annotations in the Files tab |
| Filter mode | Configurable | Configurable |
| Requires `pull-requests: write` | Yes (for `github-pr-review`) | No |
| Best for | Developer-facing feedback during review | CI gates, status checks |

Teams using Danger.js can use the [danger-plugin-no-animal-violence](https://github.com/Open-Paws/danger-plugin-no-animal-violence) instead.

---

## Documentation

- [no-animal-violence canonical rules](https://github.com/Open-Paws/no-animal-violence) — full pattern dictionary and rationale
- [no-animal-violence-action](https://github.com/Open-Paws/no-animal-violence-action) — alternative action using Check annotations
- [eslint-plugin-no-animal-violence](https://github.com/Open-Paws/eslint-plugin-no-animal-violence) — ESLint integration
- [semgrep-rules-no-animal-violence](https://github.com/Open-Paws/semgrep-rules-no-animal-violence) — Semgrep rules
- [danger-plugin-no-animal-violence](https://github.com/Open-Paws/danger-plugin-no-animal-violence) — Danger.js integration
- [reviewdog documentation](https://github.com/reviewdog/reviewdog) — upstream reviewdog project

---

<details>
<summary>Architecture</summary>

This is a composite GitHub Action — the entire implementation lives in `action.yml` and `scan.py`. No build step, no pip install, no external Python dependencies.

**Pipeline:**

```
no-animal-violence (canonical rules — embedded in scan.py)
       |
       └─> scan.py (self-contained scanner — regex engine, zero pip deps)
                  |
                  └─> reviewdog-no-animal-violence (this repo)
                             |
                             └─> GitHub PR inline comments via reviewdog
```

**Steps in `action.yml`:**

1. Install reviewdog via `reviewdog/action-setup@v1`.
2. Discover source files across the repository using `find` (filtered by extension, excluding `.git/`, `node_modules/`, `vendor/`).
3. Pass all discovered files to `scan.py` via `xargs`, which outputs one line per finding in `file:line: message` format.
4. Pipe scanner output through reviewdog using `-efm="%f:%l: %m"` so each finding maps to a specific file and line.
5. Post inline PR review comments (or check annotations, depending on `reporter`) with the phrase detected, why it is flagged, and suggested alternatives.

**Output format per finding:**
```
src/utils.py:14: "kill two birds with one stone" — Violent animal idiom with universally clearer alternatives. Consider: "accomplish two things at once", "solve two problems with one action", "hit two targets with one shot"
```

**Pattern updates:** Patterns are embedded in `scan.py`. When the canonical rules change, update `scan.py` directly.

**Tech stack:** GitHub Actions composite action · Python 3 (stdlib only) · reviewdog · Bash

</details>

---

## Contributing

Contributions are welcome from anyone who wants to make software development more consistent with animal advocacy values.

1. Clone the repo and create a feature branch.
2. Edit `scan.py` to add or update rules, or edit `action.yml` for pipeline changes.
3. Test by opening a PR (in this or another repo that uses the action) containing a known phrase from the [canonical rules](https://github.com/Open-Paws/no-animal-violence). Verify an inline comment appears on the correct diff line.
4. Run `desloppify scan --path .` — minimum score ≥85.
5. Open a PR and describe what you changed and why.

---

## License

MIT — see [LICENSE](LICENSE).

**Acknowledgments:** Built on [reviewdog](https://github.com/reviewdog/reviewdog) by the reviewdog contributors. Language patterns maintained by Open Paws in the [no-animal-violence](https://github.com/Open-Paws/no-animal-violence) repository.

---

<!-- tech_stack: GitHub Actions composite, Python, reviewdog, Bash -->
<!-- project_status: maintenance -->
<!-- difficulty: beginner -->
<!-- skill_tags: github-actions, reviewdog, speciesist-language, code-review, animal-advocacy -->
<!-- related_repos: no-animal-violence, no-animal-violence-action, no-animal-violence-pre-commit, eslint-plugin-no-animal-violence, semgrep-rules-no-animal-violence, danger-plugin-no-animal-violence -->

[Donate](https://openpaws.ai/donate) · [Discord](https://discord.gg/openpaws) · [openpaws.ai](https://openpaws.ai) · [Volunteer](https://openpaws.ai/volunteer)
