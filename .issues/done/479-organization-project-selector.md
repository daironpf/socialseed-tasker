# Issue #479: Add organization selector and multi-project context

## Description
Allow switching repositories or microservices globally from the top bar (`AppHeader`).

## Expected Behavior
- Dropdown in AppHeader showing current project/repository
- Global reactivity in Pinia: changing project automatically updates issues, components, policies, and constraints stores
- Selected project persisted in localStorage
- Visual indicator of current project context
- Project switch confirmation for unsaved changes

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Layout / Project Context

## Changes Made
1. Added `currentProject` and `availableProjects` to `uiStore` with localStorage persistence
2. Added `setProject()` action that updates currentProject and filters.project
3. Created `ProjectSelector.vue` dropdown:
   - Folder icon with current project name
   - Teleported dropdown with project list
   - Checkmark on selected project
   - Click outside to close
   - Smooth transitions
4. Integrated into AppHeader before NotificationCenter
5. 4 mock projects: SocialSeed Tasker, Auth Service, API Gateway, Data Pipeline
6. Added i18n keys for project selector (EN/ES)

## Verification
- Dropdown shows current project name
- Clicking dropdown shows project list
- Selecting project updates currentProject in store
- Selection persists on page reload via localStorage
- filters.project synced with currentProject
