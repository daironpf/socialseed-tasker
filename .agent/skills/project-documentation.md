# Skill: Project Documentation - Read & Maintain

## Description

This skill ensures the agent always reads and maintains `project.md` as the single source of truth for project structure and capabilities.

## Critical Requirement

**BEFORE ANY WORK**: Read `project.md` at the project root to understand:
- Core architecture (hexagonal structure)
- Domain model and entities
- Core actions and business logic
- Storage layer details
- CLI/API interfaces
- Testing infrastructure

## When to Read project.md

1. **At session start** - Before implementing any feature
2. **When exploring codebase** - To understand component relationships
3. **Before adding new functionality** - To ensure architectural consistency
4. **When debugging** - To understand data flow

## When to Update project.md

Update `project.md` when making changes that affect:

| Change Type | Update Required |
|-------------|-----------------|
| New CLI command | CLI Interface section |
| New API endpoint | API Interface section |
| New entity/field | Domain Model section |
| New core action | Core Actions section |
| New validation rule | Validation System section |
| New architectural pattern | Key Design Patterns section |
| New dependency/module | Package Structure section |
| Configuration change | Configuration section |
| Testing infrastructure change | Testing Infrastructure section |

## Update Guidelines

1. **Keep sections in order** - Follow existing section numbering
2. **Use existing format** - Match the documentation style
3. **Be specific** - Include code examples when adding new entities/actions
4. **Cross-reference** - Link related sections if applicable
5. **Verify after updates** - Ensure no contradictions with other docs

## Quick Reference

- **Location**: `./project.md`
- **Read first**: Always read before starting work
- **Update on**: Any structural or functional change
- **Verification**: Check consistency with `README.md` and `API_REFERENCE.md`