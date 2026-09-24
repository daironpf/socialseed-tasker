# Issue #512: Comprehensive Audit Log, Compliance & PII Redaction Suite

## Description

Las grandes organizaciones exigen auditoría completa de acciones y protección estricta de datos personales (GDPR, SOC2, HIPAA). La UI debe incluir una consola de auditoría inmutable simulada y un enmascarador interactivo de PII operativo sobre la mock API actual.

Origen: `notas.md` → Issue #504 (renumerada a #512; #504 ya está en done como Mock SSE).

## Status: DONE

> Resuelto: vista `AuditLogView` en `/audit-log` (nav Sidebar+MobileDrawer) con tabla `AuditLogTable` (actor/tipo/severidad/recurso/IP), filtros combinables (fecha, usuario, agente, tipo de evento, severidad, búsqueda), chips de contador por severidad como filtro rápido, paginación (15/pág) y exportación CSV/JSON vía `useExport` + PDF corporativo con html2canvas+jspdf sobre `#audit-log-report` (patrón Executive Dashboard). `auditLogStore` genera 84 entradas deterministas (PRNG sembrada 20260924) con 8 tipos de evento realistas; cadena de integridad mock por lotes de 12 (hash FNV enlazado + badge Verified). Suite PII: `PIIRedactionPreview` con detecciones en tiempo real (`detectPII`: tokens, API keys, correos, tarjetas, JWT...), toggle Mask PII, preview antes/después y acciones Mask/Reveal (mock); integrada en `AgentLogStream` (toggle + badge de detecciones por línea) y en `RichTextEditor` (botón escudo con preview compacta del borrador). i18n `auditLog`+`piiSuite`+`nav.auditLog` (EN/ES); `features.md` §53. `npm run build` OK.

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
- [x] `AuditLogView` with table filterable by date, user, agent, event type, severity
- [x] Export audit log as CSV, JSON, and corporate-grade PDF
- [x] Expanded PII suite previews real-time masking of tokens, API keys, emails, credit cards
- [x] PII preview works in agent log console and issue comments/descriptions
- [x] Mock audit entries realistic and stable in mock mode
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

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
