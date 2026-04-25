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

## Status: DONE ✓

## Priority: LOW

## Resolution
- Already implemented: routes are organized by domain using separate routers:
  - issues_router (issues endpoints)
  - dependencies_router (dependency endpoints)
  - components_router (component endpoints)
  - label_router (label endpoints)
  - analysis_router (analysis endpoints)
  - policy_router (policy endpoints)
  - project_router (project endpoints)
  - webhook_router (webhook endpoints)
  - agent_router (agent endpoints)
  - admin_router (admin endpoints)
  - sync_router (sync endpoints)
  - constraints_router (constraints endpoints)
- All endpoints properly separated by domain in routes.py
- File is large (2553 lines) but well-organized