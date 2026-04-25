# Issue #62: Add seed data / demo mode for first-time users

## Description

When a user starts Tasker for the first time, the system is completely empty. There is no sample data, no demo components, and no example issues to help users understand how the system works.

## Problem Found

After installing from PyPI and starting Docker Compose, the API returned empty lists for both components and issues. Users have no way to explore the dependency graph, test the analysis endpoints, or see the Kanban board in action without manually creating everything.

## Impact

- Poor first-time user experience
- Users cannot evaluate the product without significant manual setup
- Demo/sales presentations require pre-populated data
- Documentation examples cannot be tried out-of-the-box

## Suggested Fix

- Add `tasker seed` CLI command that creates sample project with components, issues, and dependencies
- Add `TASKER_DEMO_MODE=true` env var that auto-populates on first API startup
- Include a realistic example: e.g., a "microservices-platform" project with 3-4 components and 8-10 interconnected issues
- Document the seed command in README Quick Start section

## Priority

MEDIUM

## Labels

ux, onboarding, cli, feature
