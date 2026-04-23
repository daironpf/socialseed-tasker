# Workflow: Create New Issues

## When to Use

When given a requirements document or feature request that needs to be broken down into implementable issues.

## Steps

### 1. Analyze Requirements

Read the source document thoroughly. Identify:
- Distinct features or capabilities needed
- Dependencies between features
- Infrastructure/setup tasks
- Testing tasks

### 2. Create Issue Files

For each identified task, create a file in `.issues/` with the naming convention:

```
{NN}-{kebab-case-title}.md
```

Where `{NN}` is a zero-padded sequential number (01, 02, 03, etc.).

### 3. Issue File Format

```markdown
# Issue #{NN}: Descriptive Title

## Description

Detailed explanation of what needs to be built.

### Requirements

- Specific requirement 1
- Specific requirement 2

### Technical Details

Code examples, data models, API endpoints, etc.

### Business Value

Why this matters and what problem it solves.

## Status: PENDING
```

### 4. Ordering

- Number issues sequentially based on logical dependency order
- Infrastructure/setup issues should come first
- Core domain issues before entrypoints
- Tests can be part of the same issue or separate

## Rules

- Each issue should be independently implementable
- Include enough detail that an AI agent can implement without asking questions
- Include the expected file paths for new code
- Document architectural decisions and constraints
- All issue content must be in English
