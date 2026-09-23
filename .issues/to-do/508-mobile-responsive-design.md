# Issue #508: Mobile Responsive Design & Touch Navigation

## Description

El archivo de features identifica que la interfaz actual está diseñada para pantallas de escritorio. Se requiere adaptar el layout principal (Sidebar, AppHeader y IssueDetailView) para pantallas tablets y móviles, incluyendo navegación táctil y scroll horizontal.

## Status: TODO

## Priority: HIGH

## Component
Frontend / Layout / Responsive

## Implementation
1. **Sidebar Adaptativo:**
   - Ocultar `Sidebar` en pantallas < 768px (`md:hidden`)
   - Añadir botón hamburguesa en `AppHeader` para móviles
   - Crear `MobileDrawer.vue`: overlay slide-in desde la izquierda
   - Gestos de cierre: swipe left o tap en overlay
   - Transición suave (300ms)

2. **Manejo de Slide-in Panels en Móvil:**
   - `IssueDetailView`: ocupar 100% del ancho en móvil (< 768px)
   - `ComponentDetail`: mismo comportamiento
   - `ConstraintDetail`: mismo comportamiento
   - Cierre con swipe right o botón X

3. **Kanban Scroll Horizontal:**
   - Snap scrolling en columnas Kanban en pantallas estrechas
   - `scroll-snap-type: x mandatory` en contenedor
   - `scroll-snap-align: start` en cada columna
   - Indicador visual de scroll (gradient fade en bordes)

4. **Touch Optimizations:**
   - Botones mínimo 44x44px en móvil
   - Espaciado entre elementos interactivos
   - Long-press para acciones secundarias (delete, edit)

5. **Breakpoints:**
   - Mobile: < 640px (sm)
   - Tablet: 640px - 1024px (md/lg)
   - Desktop: > 1024px (xl)

## Acceptance Criteria
- [ ] Sidebar hidden on mobile, hamburger menu works
- [ ] MobileDrawer opens/closes with overlay and swipe
- [ ] IssueDetailView full-width on mobile
- [ ] Kanban columns snap-scroll on tablet
- [ ] Touch targets minimum 44x44px
- [ ] No horizontal overflow on any view
- [ ] Text readable without zoom
- [ ] All CRUD operations work on mobile
- [ ] i18n support (EN + ES)

## Files to Create
- `frontend/src/components/layout/MobileDrawer.vue`

## Files to Modify
- `frontend/src/components/layout/Sidebar.vue` — add responsive classes
- `frontend/src/components/layout/AppHeader.vue` — add hamburger button for mobile
- `frontend/src/views/IssueDetailView.vue` — responsive width
- `frontend/src/views/KanbanView.vue` — snap scrolling
- `frontend/src/views/ListView.vue` — responsive table
- `frontend/src/views/ComponentsView.vue` — responsive grid
- `frontend/tailwind.config.js` — add custom breakpoints if needed
- `frontend/src/locales/en.json` — add mobile navigation keys
- `frontend/src/locales/es.json` — add mobile navigation keys

## Related Issues
- #47 (Issue Detail Panel), #488 (Sidebar Navigation)
