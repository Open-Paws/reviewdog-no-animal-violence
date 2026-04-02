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
2. **no-animal-violence-pre-commit** (pip-installed from `Open-Paws/no-animal-violence-pre-commit`) -- the actual scanner with regex-based pattern matching
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
- Depends on [Open-Paws/no-animal-violence-pre-commit](https://github.com/Open-Paws/no-animal-violence-pre-commit) v0.2.0 for the scanner
- Depends on [reviewdog/action-setup](https://github.com/reviewdog/action-setup) for the review posting engine
