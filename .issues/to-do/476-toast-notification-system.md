# Issue #476: Implement global toast notification system

## Description
Implement a non-blocking floating toast notification manager to replace static interface alerts for success, error, warning, and info feedback.

## Expected Behavior
- Configurable positioning (default: bottom-right)
- Visual variants: `success` (green), `error` (red), `warning` (amber), `info` (blue)
- Auto-close with configurable timer (disabled for critical errors)
- Manual dismiss button (X)
- Stack multiple toasts with max limit
- Integration with Axios interceptor for automatic network error toasts (4xx/5xx)

## Status: PENDING

## Priority: HIGH

## Component
Frontend / UI / Toast Notifications

## Implementation Plan
1. Create `useToast` composable with `toast.success()`, `toast.error()`, etc.
2. Create `ToastContainer.vue` positioned bottom-right
3. Create `ToastItem.vue` with auto-close timer and dismiss button
4. Add max toast limit (5) with oldest removal
5. Integrate with Axios interceptor for automatic error toasts
6. Add i18n keys for toast messages

## Acceptance Criteria
- [ ] `useToast` composable with typed methods
- [ ] Bottom-right positioned toast container
- [ ] 4 variants: success, error, warning, info
- [ ] Auto-close timer (configurable per toast)
- [ ] Manual dismiss button
- [ ] Max 5 toasts stacked
- [ ] Axios interceptor integration
- [ ] i18n support

## Verification
- `toast.success('Saved')` shows green toast
- `toast.error('Failed')` shows red toast with longer duration
- Toasts auto-close after timeout
- X button dismisses immediately
- Network errors show automatic error toast
- Max 5 toasts displayed at once

## Related Issues
- #475 (Notification center)
