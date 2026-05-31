# Issue #373: Add .gitattributes to scaffold for Windows CRLF handling

## Description
Scaffolded files (JS, CSS, configs) use LF line endings, causing Git on Windows to show warnings about LF being replaced by CRLF. This creates noise and a poor developer experience on Windows.

## Expected Behavior
Scaffolded projects should work cleanly on Windows without git line-ending warnings.

## Actual Behavior
```
warning: in the working copy of '.agent/tasker/frontend/assets/BoardView-85y49C3b.js',
LF will be replaced by CRLF the next time Git touches it
```

## Steps to Reproduce
1. Run `tasker install .` on Windows
2. Run `git add -A`
3. Observe LF/CRLF warnings for scaffolded files

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Add a `.gitattributes` file to the scaffold template with `* text=auto` to normalize line endings automatically per platform.

## Impact
Low — cosmetic, but affects developer experience on Windows.
