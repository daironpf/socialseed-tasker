# Issue #54: Add real-time toast notifications and error handling

## Description

Implement a global toast notification system for user feedback on all API operations (success, error, warning).

### Requirements

- Enhance the `Toast.vue` component from Issue #44 into a full notification system
- Create `frontend/src/composables/useToast.ts`:
  - `showToast(message, type, duration)` - show a toast
  - `success(message)` - green success toast
  - `error(message)` - red error toast
  - `warning(message)` - amber warning toast
  - `info(message)` - blue info toast
  - Auto-dismiss after configurable duration (default 4s for success, 8s for error)
  - Stack multiple toasts (new ones appear below)
  - Manual dismiss button on each toast

- Integrate toasts into all store actions:
  - On API success: show success toast
  - On API error: show error toast with the error message from the API envelope
  - On validation errors: show inline form errors + toast

- Global error handler for unhandled API errors
- Network error detection: show "Connection lost" toast if API is unreachable

### Technical Details

- Use a reactive array of toasts in a composable
- Render toasts in a fixed-position container in `App.vue`
- Use Vue transitions for slide-in/slide-out animations
- Maximum 3 visible toasts at once, queue the rest

### Expected File Paths

- `frontend/src/composables/useToast.ts`
- `frontend/src/components/ui/ToastContainer.vue`
- Updates to all store files to integrate toasts

### Business Value

Toast notifications provide immediate feedback on user actions, making the application feel responsive and helping users understand when things go wrong.

## Status: COMPLETED
