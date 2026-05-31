# Issue #370: Windows backslashes in policies.md

## Description
File `.agent/tasker/policies.md` line 152 contains `\\s*=` which uses backslash-based escape sequences. On Windows, this can cause confusion and is inconsistent with forward-slash path normalization used elsewhere in the project.

## Expected Behavior
All file paths and regex patterns in scaffolded files should use forward slashes or be properly normalized for cross-platform compatibility.

## Actual Behavior
Backslashes appear in the generated `policies.md` file under the "No Hardcoded Secrets" policy rule, specifically in the regex pattern `"pattern:(password|api_key|secret|token)\\s*="`.

## Steps to Reproduce
1. Run `tasker install .` to scaffold a new project
2. Check `.agent/tasker/policies.md` at line 152
3. Observe the backslash pattern `\\s*=`

## Status: PENDING

## Priority: LOW

## Component
CLI / GRAPH_ENGINE

## Suggested Fix
Use raw regex pattern `\\s*=` or normalize all policy patterns to use forward slashes and proper escaping cross-platform.

## Impact
Low — minor cross-platform inconsistency, but affects Windows developer experience.
