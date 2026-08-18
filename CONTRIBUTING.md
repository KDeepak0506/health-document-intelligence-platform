# Contributing

## Development Workflow

1. Update your local `main` branch.
2. Create a feature branch from the latest `main`.
3. Work only on the assigned task.
4. Test your changes locally.
5. Make clear, focused commits.
6. Push your feature branch to GitHub.
7. Create a Pull Request.
8. Get at least one teammate approval.
9. Resolve all review comments.
10. Squash merge the Pull Request into `main`.

## Branch Naming

Use one of the following formats:

- `feature/<name>` - New functionality
- `fix/<name>` - Bug fixes
- `docs/<name>` - Documentation changes
- `refactor/<name>` - Code restructuring without changing functionality
- `test/<name>` - Adding or modifying tests

### Examples

- `feature/document-upload`
- `feature/ocr-processing`
- `feature/document-classification`
- `fix/upload-validation`
- `docs/api-documentation`
- `test/document-upload`

## Commit Messages

Use a short and descriptive commit message.

Recommended format:

`type: short description`

Examples:

- `feat: add document upload API`
- `fix: handle invalid PDF upload`
- `docs: update API documentation`
- `test: add upload validation tests`
- `refactor: simplify document service`

## Important Rules

- ❌ Never push directly to `main`.
- ❌ Never force push to `main`.
- ❌ Never commit `.env` files.
- ❌ Never commit API keys, passwords, tokens, or other secrets.
- ❌ Never commit real patient or healthcare documents.
- ❌ Do not create unrelated changes in another person's feature.
- ❌ Do not modify shared architecture or API contracts without discussing it with the team.
- ✅ Keep each Pull Request focused on one task.
- ✅ Test your changes before creating a Pull Request.
- ✅ Keep `main` in a working state.
- ✅ Ask the team before making changes that affect multiple modules.

## Pull Request Requirements

Before creating a Pull Request:

- [ ] The feature works locally.
- [ ] Tests have been run.
- [ ] No secrets or sensitive files are included.
- [ ] Only relevant files have been changed.
- [ ] The branch is up to date with `main`.

Every Pull Request requires at least **1 teammate approval** before merging.

All review comments must be resolved before merging.

Pull Requests should be **squash merged** into `main`.