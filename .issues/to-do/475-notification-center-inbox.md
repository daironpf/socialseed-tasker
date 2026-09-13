# Issue #475: Build notification center and inbox (Cmd+I)

## Description
Build a dropdown panel and standalone view for a centralized inbox to manage team and agent alerts.

## Expected Behavior
- Bell icon in `AppHeader` with unread notification count badge
- Alert categories: *Mentions*, *HITL Requests*, *Constraint Violations*, *Agent Failures*
- Filters: "All", "Unread", "Requires my action"
- Mark as read individually or bulk (Mark all as read)
- Notification detail with link to relevant issue/component
- Persistent unread state in localStorage

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Notifications / Inbox

## Implementation Plan
1. Create `NotificationCenter.vue` dropdown component
2. Create `NotificationItem.vue` with category icons and read/unread state
3. Add bell icon with badge to AppHeader
4. Implement filter tabs (All, Unread, Requires Action)
5. Add Mark All as Read functionality
6. Create notification store or extend uiStore
7. Add i18n keys for notification strings

## Acceptance Criteria
- [ ] Bell icon with unread count in AppHeader
- [ ] Dropdown with categorized notifications
- [ ] Filter by category and read status
- [ ] Mark individual/bulk as read
- [ ] Link to related issue/component
- [ ] Persistent unread state
- [ ] i18n support

## Verification
- Bell icon shows count of unread notifications
- Clicking bell opens notification dropdown
- Notifications categorized correctly
- Mark as read updates count
- Clicking notification navigates to related item

## Related Issues
- #476 (Toast notification system)
