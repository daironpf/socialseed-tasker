# Issue #55: Add dark mode, responsive design, and polish

## Description

Implement dark mode support, ensure responsive behavior across screen sizes, and add final polish to the UI.

### Requirements

- Dark mode:
  - Toggle in AppHeader (sun/moon icon)
  - Persist preference in localStorage
  - Full dark palette via Tailwind `dark:` variant
  - All components support dark mode
  - Respect `prefers-color-scheme` system preference as default

- Responsive design:
  - Board view: horizontal scroll on tablet, stacked on mobile
  - List view: table on desktop, cards on mobile
  - Sidebar: collapsible drawer on mobile
  - Modal: full-screen on mobile, centered on desktop
  - Touch-friendly tap targets (min 44px)

- Polish:
  - Smooth transitions between states
  - Hover effects on cards and buttons
  - Skeleton loading states for all async data
  - Empty states with helpful messages
  - Keyboard shortcuts: `N` new issue, `/` focus search, `B` board view, `L` list view
  - Favicon with SocialSeed branding
  - Page title updates with current view

### Technical Details

- Tailwind dark mode strategy: `darkMode: 'class'`
- Toggle adds/removes `dark` class on `<html>` element
- Use CSS transitions for smooth theme changes
- Responsive breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)

### Expected File Paths

- Updates to `tailwind.config.ts` for dark mode
- Updates to `frontend/src/components/layout/AppHeader.vue` for toggle
- New `frontend/src/composables/useDarkMode.ts`
- Updates to all component files for `dark:` variants

### Business Value

Dark mode and responsive design make the application comfortable to use on any device and in any lighting condition, significantly improving the user experience.

## Status: COMPLETED
