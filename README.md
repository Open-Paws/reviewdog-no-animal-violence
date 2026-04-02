# reviewdog-no-animal-violence

A [reviewdog](https://github.com/reviewdog/reviewdog) runner for detecting speciesist language in pull requests.

Wraps [no-animal-violence-pre-commit](https://github.com/Open-Paws/no-animal-violence-pre-commit) to automatically flag speciesist terms and suggest inclusive alternatives directly on PR diffs.

## Usage

Add the following to `.github/workflows/speciesism.yml` in your repository:

```yaml
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

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `github_token` | GitHub token for reviewdog API access | `${{ github.token }}` |
| `level` | Report level: `info`, `warning`, or `error` | `warning` |
| `reporter` | reviewdog reporter: `github-pr-check`, `github-pr-review`, or `github-check` | `github-pr-review` |
| `filter_mode` | Filtering mode: `added`, `diff_context`, `file`, or `nofilter` | `added` |

## Filter Modes

- **`added`** (default) — Only flag speciesist language in newly added lines. Best for incremental adoption.
- **`diff_context`** — Flag in added lines and surrounding context.
- **`file`** — Flag in any file that was modified in the PR.
- **`nofilter`** — Flag across the entire repository.

## Supported File Types

The scanner checks the following file types:

`.py`, `.js`, `.ts`, `.md`, `.txt`, `.rst`, `.yaml`, `.yml`, `.go`, `.rs`, `.java`, `.rb`

Directories `.git/`, `node_modules/`, and `vendor/` are excluded.

## What It Detects

The scanner identifies speciesist language patterns — phrases that normalize the exploitation or objectification of non-human animals — and suggests alternatives. For example:

- "kill two birds with one stone" -> "feed two birds with one scone"
- "beat a dead horse" -> "feed a fed horse"
- "guinea pig" (as verb) -> "test subject"

See the [no-animal-violence-pre-commit](https://github.com/Open-Paws/no-animal-violence-pre-commit) repo for the full term list.

## License

MIT
