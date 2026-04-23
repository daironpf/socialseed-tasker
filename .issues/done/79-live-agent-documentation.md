# Issue #79: Live Agent Documentation

## Description

Implement dynamic "Dynamic Progress Manifest" within issue descriptions. Agents must maintain real-time documentation of their work progress, including TODO lists, affected files, and technical debt notes.

## Requirements

- Implement live TODO list in issue description with checkboxes updated as agent completes sub-tasks
- Add "Affected Files" section updated in real-time with created or modified file paths
- Add "Technical Debt Notes" section for observations made during implementation
- Create API endpoints to update these sections
- Preserve original issue description while appending manifest sections

## Technical Details

### Manifest Structure
```markdown
## Agent Progress Manifest

### Live TODO
- [ ] Sub-task 1
- [x] Sub-task 2

### Affected Files
- src/core/module.ts
- tests/unit/test_module.py

### Technical Debt Notes
- Note about temporary workaround
- TODO for future refactoring
```

### API Endpoints
- `PATCH /issues/{id}/manifest/todo` - Update TODO list
- `PATCH /issues/{id}/manifest/files` - Update affected files
- `PATCH /issues/{id}/manifest/notes` - Update technical debt notes
- `GET /issues/{id}/manifest` - Get full manifest

### Implementation Location
- Update issue entity to include manifest fields
- Add manifest update actions in core/
- Create API endpoints in entrypoints/web_api/
- Update CLI to display manifest

## Business Value

Enables human oversight of AI agent progress without interrupting their work. Provides real-time visibility into what files are being modified and what decisions are being made.

## Status: COMPLETED