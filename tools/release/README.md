Changelog Generator

Usage
- Local generate:
  python tools/release/changelogctl.py generate --from v1.2.0 --to v1.3.0 --out CHANGELOG.md

Environment
- RELEASE_GH_TOKEN optional GitHub token to enrich PR metadata.
- RELEASE_GH_REPO repo slug like owner/repo when using token.

Templates
- Default templates live in tools/release/templates.
- Template variables: groups, from_ref, to_ref, generated_at.

CI
- ci/release-changelog.yml runs on tag push and produces releases/<tag>.md artifact.

Determinism
- Commits are sorted by commit date (ISO) then hash.
- PRs are sorted by number ascending.
