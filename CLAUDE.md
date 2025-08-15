# Claude Development Guidelines

This document contains important rules and guidelines for working on this codebase, derived from experience and best practices established during development.

## Testing and Debugging Guidelines

### Debug Script Organization
- **For transient debugging scripts**: Put them in `test/oneoff`
- **Add context documentation**: Include description of the context and what problem they're debugging in the test file
- **Add creation dates**: Include the date of creation to all oneoff scripts
- **Purpose**: Keeps temporary debugging code organized and documented

### Test Documentation Strategy
- **Individual file documentation**: Move all descriptions of individual test files used as input to tests to the individual source files to make it more maintainable
- **Minimal central documentation**: Don't backlink test documentation files to the test code - make test docs among test files very simple because they won't be maintained frequently
- **Purpose**: Reduces maintenance burden and keeps docs current

### Test Execution Standards
- **Quality checks required**: When completing a task, MUST run lint and typecheck commands (e.g., ruff, npm run lint, npm run typecheck) if they were provided to ensure code is correct
- **Command documentation**: If unable to find the correct command, ask the user and suggest writing it to CLAUDE.md for future reference
- **Purpose**: Ensures code quality and prevents regressions

## Code Quality and Safety

### Security Guidelines
- **No secrets in repository**: NEVER commit secrets or keys to the repository
- **Security best practices**: Always follow security best practices
- **No secret exposure**: Never introduce code that exposes or logs secrets and keys
- **Purpose**: Maintains repository security

### Code Style Standards
- **No unnecessary comments**: DO NOT ADD ***ANY*** COMMENTS unless asked, or unless documenting a particularly hairy section of code
- **Follow existing conventions**: When making changes to files, first understand the file's code conventions and mimic them
- **Use existing patterns**: Use existing libraries and utilities, follow existing patterns
- **Library verification**: NEVER assume a library is available - check that the codebase already uses it first
- **Purpose**: Maintains consistency and reduces unnecessary clutter

### Documentation Standards
- **No proactive documentation**: NEVER proactively create documentation files (*.md) or README files unless explicitly requested. If documentation is a good idea, recommend it to the user
- **Prefer editing over creating**: ALWAYS prefer editing existing files to creating new ones
- **Minimal file creation**: NEVER create files unless absolutely necessary for achieving the goal
- **Preserving existing organization**: When adding a doc file, review the existing doc organization to make sure it's added in the proper place and is easily discoverable
- **Purpose**: Prevents documentation bloat and maintenance overhead

## Development Workflow

### File Management
- **Document plans**: Before starting to edit code, document your plan with the date in the `docs/plans` folder. After completing, document your results at the end of the same file with an executive summary
- **Edit over create**: ALWAYS prefer editing an existing file to creating a new one
- **Read before edit**: Use Read tool at least once before editing any file
- **Purpose**: Maintains codebase integrity and intentionality

### Code Edits
- **Test significant changes**: For significant code changes, use comprehensive test validation
- **Maintain formatting**: ALWAYS run `ruff format` to format code that you edit
- **Purpose**: Maintains code style and prevents breaking changes

### Task Management
- **Use TodoWrite frequently**: Use TodoWrite tool frequently to track tasks and give user visibility into progress
- **Immediate completion marking**: Mark todos as completed immediately after finishing - don't batch completions
- **Single active task**: Only have ONE task in_progress at any time
- **Purpose**: Provides transparency and ensures systematic completion

## Quality Commands

Add project-specific lint/typecheck commands here:

```bash
# Example commands (update as needed):
# npm run lint
# npm run typecheck
# ruff format
```

---

*This file is automatically updated based on development experience and should be referenced before starting work on this codebase.*