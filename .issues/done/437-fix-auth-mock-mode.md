# Issue #437: Fix auth LoginScreen blocking mock mode

## Description
When `USE_MOCK = true`, `authStore.isAuthenticated` evaluates to `false` because `API_KEY` is empty. This forces users to "authenticate" even though mock mode doesn't use API keys. Additionally, `LoginScreen` calls `window.location.reload()` AND `App.vue` also calls it via `onLoggedIn`, causing a double-reload.

## Expected Behavior
- In mock mode, app opens directly without login screen
- No double page reload

## Status: COMPLETED

## Priority: CRITICAL

## Component
Frontend / Auth

## Changes Made
1. `authStore.ts`: `isAuthenticated` now returns `true` when `USE_MOCK = true`
2. `LoginScreen.vue`: Removed redundant `window.location.reload()` in `handleLogin()`
3. `LoginScreen.vue`: Removed broken `client.defaults.headers.common['X-API-Key']` access on mockClient
4. `LoginScreen.vue`: `handleUnauthorized` only reloads in non-mock mode

## Verification
- App opens directly in mock mode without login screen
- No double page reload on authentication

## Related Issues
- None
