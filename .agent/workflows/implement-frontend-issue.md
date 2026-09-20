# Workflow: Implement Frontend UI Issue

## When to Use
When instructed to implement a frontend UI issue (issues in the `to-do` folder with `Frontend` component).

## Prerequisites
- Node.js 18+ installed
- Python 3.10+ (for local mock-api)
- Read `.agent/skills/frontend-ui-development.md` for patterns and conventions

---

## Steps

### 1. Read the Issue
Read the issue file from `.issues/to-do/` to understand:
- Description and expected behavior
- Acceptance criteria
- Implementation plan
- Related issues

### 2. Understand the Scope
Determine what needs to be created/modified:
- **New View**: Create `src/views/FeatureView.vue`
- **New Store**: Create `src/stores/featureStore.ts`
- **New Types**: Create `src/types/feature.ts`
- **New Components**: Create in appropriate `src/components/` subdirectory
- **Route**: Add to `src/router/index.ts`
- **Sidebar**: Add nav item to `src/components/layout/Sidebar.vue`
- **Header**: Add title mapping to `src/components/layout/AppHeader.vue`
- **i18n**: Add keys to `src/locales/en.json` and `src/locales/es.json`

### 3. Create Types First
Always create type definitions before stores or components:
```bash
# File: src/types/feature.ts
```

### 4. Create Store with Mock Data
Create Pinia store with in-memory mock data:
```bash
# File: src/stores/featureStore.ts
```
- Define `MOCK_*` const array
- Implement CRUD operations
- Use `setTimeout` for simulated delay
- Export computed getters

### 5. Create View Component
Build the main view following existing patterns:
```bash
# File: src/views/FeatureView.vue
```
- Use `useI18n()` for all text
- Support dark mode on all elements
- Follow card/table/modal patterns from existing views
- Import and use store

### 6. Create Supporting Components
If the view needs sub-components:
```bash
# File: src/components/feature/FeatureCard.vue
# File: src/components/feature/FeatureModal.vue
```

### 7. Add Route, Sidebar, Header
```typescript
// router/index.ts
{ path: '/feature', name: 'Feature', component: () => import('@/views/FeatureView.vue') }

// Sidebar.vue - add to appropriate nav group
{ path: '/feature', label: t('nav.feature'), icon: 'SVG_PATH' }

// AppHeader.vue - add to pageTitle mapping
'/feature': t('header.feature'),
```

### 8. Add i18n Keys
Add to BOTH `en.json` and `es.json`:
```json
{
  "nav": { "feature": "Feature" },
  "header": { "feature": "Feature" },
  "feature": { "title": "...", "subtitle": "...", ... }
}
```

### 9. Build and Verify
```bash
cd frontend && npm run build
```
Fix any TypeScript errors (unused imports, missing types).

### 10. Local Testing
```bash
# Terminal 1: Mock API
cd mock-api
$env:DATA_DIR="..\frontend\dataset-de-pruebas"
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```
Navigate to `http://localhost:5173/feature` and verify.

### 11. Docker Build (Optional)
```bash
cd frontend && npm run build
docker compose --profile api build --no-cache tasker-board
docker compose --profile api up -d
```

### 12. Move Issue to Done
```bash
# Update status in issue file
## Status: DONE

# Check acceptance criteria
- [x] Criterion 1
- [x] Criterion 2

# Move file
Move-Item .issues/to-do/NNN-issue.md .issues/done/NNN-issue.md
```

### 13. Commit and Push
```bash
git add <files>
git commit -m "feat: implement <feature> (Issue #NNN)"
git push origin main
```

---

## Checklist
- [ ] Issue requirements fully understood
- [ ] Types defined
- [ ] Store created with mock data
- [ ] View component created
- [ ] Supporting components created
- [ ] Route added
- [ ] Sidebar nav item added
- [ ] Header title mapping added
- [ ] i18n keys added (EN + ES)
- [ ] Dark mode supported on all elements
- [ ] Build passes (`npm run build`)
- [ ] Local testing successful
- [ ] Issue moved to done
- [ ] Committed and pushed
