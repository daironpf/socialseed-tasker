# Workflow: UI Review and Fix

## When to Use
When instructed to review the UI for issues (visual bugs, accessibility, dark mode, i18n, UX problems) and fix them.

## Prerequisites
- Frontend dev server running (`npm run dev`)
- Read `.agent/skills/frontend-ui-development.md` for conventions

---

## Review Categories

### 1. Dark Mode Issues
Check every component for:
- Missing `dark:` variants on backgrounds, borders, text
- Hardcoded colors that don't adapt to dark mode
- Checkbox/select elements missing dark borders
- Icons not visible in dark mode

**Common fixes:**
```html
<!-- Before -->
<div class="bg-white border-gray-200">

<!-- After -->
<div class="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
```

### 2. i18n Issues
Check for:
- Hardcoded strings in templates (English text not wrapped in `t()`)
- Missing keys in one locale but present in the other
- Hardcoded roles/labels (e.g., "admin" instead of `t('roles.admin')`)
- Aria-labels not using `t()`

**Common fixes:**
```html
<!-- Before -->
<span>Active</span>

<!-- After -->
<span>{{ t('feature.active') }}</span>
```

### 3. Accessibility Issues
Check for:
- Icon-only buttons without `aria-label`
- Missing `role` attributes on interactive elements
- Low contrast text
- Missing keyboard navigation support

**Common fixes:**
```html
<!-- Before -->
<button @click="close"><svg>...</svg></button>

<!-- After -->
<button :aria-label="t('common.close')" @click="close"><svg>...</svg></button>
```

### 4. UX Consistency Issues
Check for:
- Inconsistent spacing/padding across similar components
- Different button styles for same actions
- Missing loading states
- Missing empty states
- Missing error states

### 5. Memory Leaks
Check for:
- `setTimeout`/`setInterval` without cleanup in `onUnmounted`
- Event listeners not removed
- Watchers not stopped

**Common fixes:**
```typescript
// Before
setTimeout(() => { ... }, 1000)

// After
const timeout = setTimeout(() => { ... }, 1000)
onUnmounted(() => clearTimeout(timeout))
```

---

## Review Process

### Step 1: Identify Target Files
```bash
# List all Vue files
find frontend/src -name "*.vue" -type f

# Search for hardcoded strings
grep -rn "class=\".*\"" frontend/src/views/ --include="*.vue" | grep -v "dark:"

# Search for missing aria-labels
grep -rn "<button" frontend/src/views/ --include="*.vue" | grep -v "aria-label"
```

### Step 2: Read and Analyze
Read each target file and categorize issues.

### Step 3: Fix Issues
Apply fixes following the patterns in `skills/frontend-ui-development.md`.

### Step 4: Build and Verify
```bash
cd frontend && npm run build
```
Fix any TypeScript errors.

### Step 5: Local Test
Verify fixes visually in the browser (dark mode + light mode).

### Step 6: Commit
```bash
git add <files>
git commit -m "fix: <description> (UI review pass N)"
git push origin main
```

---

## Common Fix Patterns

### Dark Mode Checkbox
```html
<input type="checkbox" class="h-4 w-4 rounded border-gray-300 dark:border-gray-600">
```

### Dark Mode Close Button
```html
<button class="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-500">
```

### Dark Mode Select
```html
<select class="border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-700 dark:text-white">
```

### i18n Fallback
```typescript
// In computed or template
const label = computed(() => t(`feature.${props.type}`) || props.type)
```

### setTimeout Cleanup
```typescript
const timeout = ref<ReturnType<typeof setTimeout>>()

onUnmounted(() => {
  if (timeout.value) clearTimeout(timeout.value)
})
```

---

## Checklist
- [ ] All views reviewed for dark mode
- [ ] All hardcoded strings replaced with `t()`
- [ ] Both locales (EN/ES) in sync
- [ ] Icon-only buttons have aria-labels
- [ ] No memory leaks (setTimeout cleanup)
- [ ] Build passes
- [ ] Visual verification in both modes
- [ ] Changes committed
