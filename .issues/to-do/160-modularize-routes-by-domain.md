# Issue #164: Modularize Routes by Domain

## Description
Split the monolithic API routes into domain-specific modules for better maintainability and organization.

## Expected Behavior
API routes should be organized by domain (issues, components, dependencies, etc.) in separate modules.

## Actual Behavior
Current routes may be in a monolithic file that needs separation.

## Steps to Reproduce
1. Review the current API route structure
2. Identify the different domains
3. Plan the modularization

## Status: PENDING

## Priority: LOW

## Recommendations
- Create domain-specific route modules:
  - `routes/issues.py`
  - `routes/components.py`
  - `routes/dependencies.py`
  - `routes/analysis.py`
  - `routes/constraints.py`
  - `routes/policies.py`
  - `routes/sync.py`
  - `routes/webhooks.py`
  - `routes/admin.py`
- Import and include routers in main app
- Ensure backward compatibility during transition
- Add tests for each domain route module