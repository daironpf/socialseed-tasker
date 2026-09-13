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

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Notifications / Inbox

## Changes Made
1. Created `notifications.ts` types with `AppNotification` interface and `NotificationCategory` type
2. Created `notificationsStore.ts` with:
   - localStorage persistence for unread state
   - `addNotification()`, `markAsRead()`, `markAllAsRead()`, `dismiss()` actions
   - `unreadCount` and `unreadByCategory` computed properties
   - `getFiltered()` for tab filtering
   - Mock notification seeding (6 sample notifications)
3. Created `NotificationItem.vue` component:
   - Category icon with color coding
   - Read/unread visual state (blue bg for unread)
   - "ACTION" badge for requiresAction notifications
   - Relative time display (just now, Xm ago, Xh ago, Xd ago)
   - Dismiss button on hover
   - Click navigates to linked issue/component
4. Created `NotificationCenter.vue` dropdown:
   - Bell icon with red unread count badge (99+ cap)
   - Teleported dropdown panel with filter tabs (All/Unread/Requires Action)
   - Mark all as read button
   - Empty state with bell icon
   - Click outside to close
5. Integrated into AppHeader next to UserMenu
6. Added i18n keys for notifications UI (EN/ES)

## Verification
- Bell icon shows unread count in header
- Clicking bell opens notification dropdown
- Notifications categorized with colored icons
- Filter tabs work (All/Unread/Action)
- Mark all as read clears all unread states
- Clicking notification navigates to linked item
- State persists across page reloads
