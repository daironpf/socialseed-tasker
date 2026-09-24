# Issue #512: Comprehensive Audit Log, Compliance & PII Redaction Suite

## Description

Las grandes organizaciones exigen auditoría completa de acciones y protección estricta de datos personales (GDPR, SOC2, HIPAA). La UI debe incluir una consola de auditoría inmutable simulada y un enmascarador interactivo de PII operativo sobre la mock API actual.

Origen: `notas.md` → Issue #504 (renumerada a #512; #504 ya está en done como Mock SSE).

## Status: TODO

## Priority: HIGH

## Component
Frontend / Compliance / Audit / PII

## Type
feat / compliance

## Implementation
1. **Vista `AuditLogView`:**
   - Nueva ruta `/audit-log` (global; no confundir con AuditTrail por issue)
   - Tabla de registros filtrable por: fecha (rango), usuario, agente, tipo de evento, nivel de severidad
   - Datos mock: extender dataset o generar en store (~50–100 entradas realistas: status change, HITL, policy violation, agent run, login, export, governance override)
   - Paginación + búsqueda de texto

2. **Exportación corporativa:**
   - CSV y JSON vía `useExport` (ya existente)
   - PDF de grado corporativo: html2canvas + jspdf (patrón de Executive Dashboard) sobre la vista de tabla o reporte resumido

3. **Suite PII interactiva:**
   - Ampliar `piiDetector.ts` (si hace falta) y exponer previsualización en tiempo real del enmascaramiento de: tokens, API keys, correos, tarjetas de crédito
   - Integrar en: consola de logs del agente (`AgentLogStream` / AI Reasoning) y comentarios/descripción de issues (RichTextEditor o preview)
   - UI de redacción: toggle "Mask PII" con preview before/after; acciones Mask / Reveal (mock)

4. **Consola inmutable simulada:**
   - Indicador de hash/cadena de auditoría mock por lote de eventos
   - Filtros combinables + contador de eventos por severidad

## Acceptance Criteria
- [ ] `AuditLogView` with table filterable by date, user, agent, event type, severity
- [ ] Export audit log as CSV, JSON, and corporate-grade PDF
- [ ] Expanded PII suite previews real-time masking of tokens, API keys, emails, credit cards
- [ ] PII preview works in agent log console and issue comments/descriptions
- [ ] Mock audit entries realistic and stable in mock mode
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/views/AuditLogView.vue`
- `frontend/src/components/audit/AuditLogTable.vue`
- `frontend/src/components/pii/PIIRedactionPreview.vue`
- `frontend/src/stores/auditLogStore.ts`
- `frontend/src/types/auditLog.ts`
- `frontend/dataset-de-pruebas/audit-log.json` (optional)

## Files to Modify
- `frontend/src/router/index.ts` — `/audit-log`
- `frontend/src/components/layout/Sidebar.vue` / `MobileDrawer.vue` — nav entry
- `frontend/src/utils/piiDetector.ts` — extended patterns + preview helpers if needed
- `frontend/src/components/ui/AgentLogStream.vue` — PII mask toggle
- `frontend/src/components/ui/RichTextEditor.vue` or `IssueDetailView.vue` — issue comment PII preview
- `mock-api/server.py` — optional audit endpoints
- `frontend/src/locales/en.json` / `es.json` — auditLog, piiSuite sections
- `features.md` — when done

## Related Issues
- #478 (Audit Trail Per Issue), #496 (PII & Secrets Guardrail), #317 (Data Retention / GDPR backend), #19 (Export & Data Features), #21 (Notifications)
