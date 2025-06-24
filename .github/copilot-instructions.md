# Project Policy

This policy provides a single, authoritative, and machine-readable source of truth for AI coding agents and humans, ensuring that all work is governed by clear, unambiguous rules and workflows. It aims to eliminate ambiguity, reduce supervision needs, and facilitate automation while maintaining accountability and compliance with best practices.

# Docs

The `docs/` directory is the authoritative source of truth for all project documentation, including:
- Tasks
- Architectural decisions
- Technical documentation
- Test plans and results
- User guides and manuals

The AI_Agent must read the relevant documentation from the `docs/` directory to ensure it has the most up-to-date information before proceeding with any work.
After any change, the AI_Agent must ensure that all relevant documentation is updated to reflect the current state of the project.

# Project

- Frontend uses bun.
- Servers run in a background task with hot reload.
- Installing deps:
  - Backend: `${workspaceDir}$ uv add <package>`
  - Frontend: `${workspaceDir}/src/tree_sprawler/viz/frontend$ bun add <package>`

# Fundamental Principles

1. **External Package Research and Documentation**: For any proposed tasks that involve external packages, to avoid hallucinations, use the web to research the documentation first to ensure it's 100% clear how to use the API of the package. Then for each package, a document should be created `<task id>-<package>-guide.md` that contains a fresh cache of the information needed to use the API. It should be date-stamped and link to the original docs provided. E.g., if pg-boss is a library to add as part of task 2-1 then a file `tasks/2-1-pg-boss-guide.md` should be created. This documents foundational assumptions about how to use the package, with example snippets, in the language being used in the project.
2. **Task Granularity**: Tasks must be defined to be as small as practicable while still representing a cohesive, testable unit of work. Large or complex features should be broken down into multiple smaller tasks.
3. **Don't Repeat Yourself (DRY)**: Information should be defined in a single location and referenced elsewhere to avoid duplication and reduce the risk of inconsistencies. Specifically:
    - Task information should be fully detailed in their dedicated task files and only referenced from other documents.
    - The only exception to this rule is for titles or names (e.g., task names in lists).
    - Any documentation that needs to exist in multiple places should be maintained in a single source of truth and referenced elsewhere.
4. **Use of Constants for Repeated or Special Values**: Any value (number, string, etc.) used more than once in generated code—especially "magic numbers" or values with special significance—**must** be defined as a named constant.
    - Example: Instead of `for (let i = 0; i < 10; i++) { ... }`, define `const numWebsites = 10;` and use `for (let i = 0; i < numWebsites; i++) { ... }`.
    - All subsequent uses must reference the constant, not the literal value.
    - This applies to all code generation, automation, and manual implementation within the project.
5. **Technical Documentation for APIs and Interfaces**: As part of completing any task that creates or modifies APIs, services, or interfaces, technical documentation must be created or updated explaining how to use these components. This documentation should include:
    - API usage examples and patterns
    - Interface contracts and expected behaviors  
    - Integration guidelines for other developers
    - Configuration options and defaults
    - Error handling and troubleshooting guidance
    - The documentation must be created in the appropriate location (e.g., `docs/` or inline code documentation).
