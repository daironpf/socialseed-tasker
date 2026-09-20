# Skill: Frontend UI Development

## Description
Specialized skill for working on the SocialSeed Tasker Vue 3 frontend UI. Covers component creation, store management, i18n, routing, and UI-specific patterns.

---

## Tech Stack
- **Framework**: Vue 3.5 + TypeScript + Composition API (`<script setup>`)
- **Build**: Vite 6
- **Styling**: Tailwind CSS 3 (dark mode via `class` strategy)
- **State**: Pinia (Composition API style)
- **Routing**: Vue Router (lazy-loaded routes)
- **i18n**: vue-i18n (`legacy: false`, `localStorage` persistence)
- **HTTP**: Axios with mock interceptor (`USE_MOCK = true`)

---

## Project Structure

```
frontend/src/
├── views/              # Page-level components (one per route)
├── components/
│   ├── layout/         # Sidebar, AppHeader, UserMenu, NavItem
│   ├── ui/             # Reusable UI (DiffViewer, AuditTrail, Toast, etc.)
│   ├── board/          # Kanban-specific (IssueCard, KanbanColumn)
│   ├── dashboard/      # Dashboard charts and stats
│   ├── analysis/       # Impact analysis, Root cause
│   ├── chat/           # Chat system (ChatView, FloatingChat, etc.)
│   └── users/          # User/Agent modals
├── stores/             # Pinia stores (10 stores)
├── composables/        # Vue composables (useToast, useExport, etc.)
├── api/                # API client (client.ts, mockApi.ts, *Api.ts)
├── locales/            # i18n (en.json, es.json)
├── types/              # TypeScript types (index.ts, chat.ts, audit.ts, etc.)
└── router/             # Vue Router config
```

---

## File Creation Patterns

### 1. New View (Page)
```bash
# File: src/views/FeatureView.vue
<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('feature.title') }}
      </h2>
    </div>
    <!-- Content -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

onMounted(() => {
  // Load data
})
</script>
```

### 2. New Pinia Store
```bash
# File: src/stores/featureStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useFeatureStore = defineStore('feature', () => {
  const items = ref<ItemType[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchItems() {
    loading.value = true
    error.value = null
    try {
      // Mock data or API call
      items.value = [...MOCK_DATA]
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, fetchItems }
})
```

### 3. New Type Definition
```bash
# File: src/types/feature.ts
export type FeatureStatus = 'active' | 'inactive' | 'pending'

export interface Feature {
  id: string
  name: string
  status: FeatureStatus
  createdAt: string
}
```

### 4. Adding i18n Keys
```json
// In en.json and es.json
{
  "feature": {
    "title": "Feature Name",
    "subtitle": "Description",
    "actions": {
      "create": "Create",
      "edit": "Edit",
      "delete": "Delete"
    }
  }
}
```

### 5. Adding a Route
```typescript
// In src/router/index.ts
{ path: '/feature', name: 'Feature', component: () => import('@/views/FeatureView.vue') }
```

### 6. Adding Sidebar Nav Item
```typescript
// In src/components/layout/Sidebar.vue navGroups
{ path: '/feature', label: t('nav.feature'), icon: 'M...' }
```

---

## Dark Mode Checklist
Every component MUST support dark mode:
- [ ] Backgrounds: `bg-white dark:bg-gray-800`
- [ ] Borders: `border-gray-200 dark:border-gray-700`
- [ ] Text: `text-gray-900 dark:text-white` (primary), `text-gray-500 dark:text-gray-400` (secondary)
- [ ] Inputs: `bg-gray-50 dark:bg-gray-700` with `border-gray-300 dark:border-gray-600`
- [ ] Hover states: `hover:bg-gray-50 dark:hover:bg-gray-700/30`

---

## i18n Checklist
- [ ] All user-visible text uses `t('key')`
- [ ] Both `en.json` and `es.json` have matching keys
- [ ] Aria-labels on icon-only buttons use `t()`
- [ ] Placeholders use `t()`
- [ ] Error/success messages use `t()`

---

## Component Styling Patterns

### Cards
```html
<div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
```

### Buttons
```html
<!-- Primary -->
<button class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">

<!-- Secondary -->
<button class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700">

<!-- Danger -->
<button class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
```

### Status Badges
```html
<span class="rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
```

### Tables
```html
<table class="w-full">
  <thead>
    <tr class="border-b border-gray-200 dark:border-gray-700">
      <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
```

---

## Mock Data Pattern
Stores with mock data should:
1. Define `MOCK_*` const array at top of file
2. Use `setTimeout` to simulate network delay (300ms)
3. Support CRUD operations on the in-memory array
4. NOT import from `@/api/*` (use direct mock data)

---

## Build & Deploy Commands

```bash
# Type check
cd frontend && npm run build  # includes vue-tsc

# Dev server (local)
npm run dev  # http://localhost:5173

# Production build
npm run build  # outputs to dist/

# Docker rebuild
docker compose --profile api build --no-cache tasker-board
docker compose --profile api up -d
```

---

## Common Gotchas

1. **Unused imports cause build errors** — `vue-tsc` is strict. Remove unused imports before building.
2. **`window as any`** — Used in `client.ts` for `__API_URL__` / `__API_KEY__`. Acceptable pattern.
3. **Hyper-V port conflict** — Ports 8801-8900 reserved on Windows. Use temp ports 19000-19002 for Docker, revert before commit.
4. **Mock API proxy** — Local dev requires Vite proxy: `/mock-api` → `http://localhost:8001` with path rewrite.
5. **i18n key sync** — Always add keys to both `en.json` and `es.json`.
