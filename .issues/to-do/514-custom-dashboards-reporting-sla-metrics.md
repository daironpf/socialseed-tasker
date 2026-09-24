# Issue #514: Custom Dashboards, Reporting Engine & SLA Metric Tracking

## Description

Los ejecutivos de ingeniería y líderes de equipo necesitan paneles analíticos visuales para medir el ROI de los agentes, tiempo de resolución de incidentes (MTTR) y cumplimiento de SLAs, con informes descargables para stakeholders.

Origen: `notas.md` → Issue #506 (renumerada a #514; #506 ya está en done como Diff Preview).

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Analytics / Dashboards / SLA

## Type
feat / analytics

## Implementation
1. **Vista `AnalyticsDashboardView` (Reporting):**
   - Nueva ruta `/analytics` (o `/reports`)
   - Gráficos interactivos mock:
     - MTTR antes vs. después de agentes (líneas/grupos comparativos)
     - Tasa de resolución autónoma (auto-healing success rate) — alinear con datos de `autoHealingStore`
     - Consumo de presupuesto en USD por proyecto (extender `finopsStore` / datos por `project_id`)
   - Rango de fechas + comparación period-to-period

2. **Panel de control de SLAs (`SLAMetricsCard`):**
   - Indicadores visuales de brecha de tiempo (dentro de SLA / en riesgo / incumplido)
   - Notificaciones de riesgo de incumplimiento (integrar `notificationsStore` o banner local)
   - SLAs mock por prioridad/proyecto (ej. CRITICAL 4h, HIGH 24h, MEDIUM 72h)

3. **Motor de informes (`ReportExporter`):**
   - Botón "Generar Informe Semanal/Mensual para Ejecutivos"
   - Resumen visual interactivo (KPIs top + charts + tabla de excepciones)
   - Descarga PDF/PNG vía html2canvas + jspdf (patrón Executive Dashboard) y/o JSON

4. **Store:**
   - `analyticsReportStore` con métricas derivadas de issues + finops + auto-healing mock
   - No depende de backend real

## Acceptance Criteria
- [ ] Interactive charts: MTTR before vs after agents, auto-healing success rate, USD budget by project
- [ ] SLA control panel with time-gap indicators and breach-risk notifications
- [ ] Weekly/Monthly executive report generator with interactive visual summary and download
- [ ] Date range and period comparison work on mock data
- [ ] Consistent with existing Executive / FinOps / Auto-Healing stores where data overlaps
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/views/AnalyticsDashboardView.vue`
- `frontend/src/components/analytics/SLAMetricsCard.vue`
- `frontend/src/components/analytics/ReportExporter.vue`
- `frontend/src/components/analytics/MTTRComparisonChart.vue`
- `frontend/src/stores/analyticsReportStore.ts`
- `frontend/src/types/analytics.ts`

## Files to Modify
- `frontend/src/router/index.ts` — `/analytics`
- `frontend/src/components/layout/Sidebar.vue` / `MobileDrawer.vue` — nav entry
- `frontend/src/stores/finopsStore.ts` / `autoHealingStore.ts` / `executiveStore.ts` — shared metric helpers if needed
- `frontend/src/stores/notificationsStore.ts` — SLA risk notifications (optional)
- `frontend/src/locales/en.json` / `es.json` — analytics, sla sections
- `features.md` — when done

## Related Issues
- #497 (Executive Dashboard), #493 (Agent FinOps Dashboard), #494 (Auto-Healing Pipeline Monitor), #4 (Dashboard BoardView), #19 (Export)
