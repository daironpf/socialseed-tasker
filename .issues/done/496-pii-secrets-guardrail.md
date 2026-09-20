# Issue #496: Add Real-time PII & Sensitive Secrets Guardrail Warnings

## Description
Sensitive data (API keys, passwords, PII) must not leak into LLM prompts or Neo4j persistent storage. Client-side and streaming regex scanners are needed to flag potential sensitive data in chat inputs and logs.

## Status: DONE

## Priority: HIGH

## Component
Frontend / Chat / Security

## Implementation
1. Created `utils/piiDetector.ts` — 10 regex patterns (API keys, JWT, private keys, passwords, tokens, emails, phones, SSN, credit cards, IPs) with detection, redaction, severity levels
2. Created `components/chat/PIIDetectionBanner.vue` — live detection banner with severity colors
3. Created `components/chat/PIIWarningModal.vue` — warning modal with Cancel/Mask & Send/Send Anyway actions
4. Modified `components/chat/ChatInput.vue` — integrated PII detection, amber border on detection, modal on critical PII
5. Added i18n keys (EN + ES) for pii section

## Acceptance Criteria
- [x] Live detection in chat input
- [x] Detection banner for API keys, tokens, emails
- [x] Automated redacting in log outputs
- [x] Warning modal blocking submission
- [x] Confirm/mask actions for sensitive data
- [x] Pattern library for common secrets (10 patterns)
- [x] i18n support

## Verification
- Type API key (e.g., sk-...) in chat input -> see red detection banner
- Try to submit -> warning modal appears
- Choose "Mask & Send" -> submission proceeds with redacted text
- Type email -> see amber detection banner
- Type password -> see red detection banner
- Choose "Send Anyway" -> submission proceeds with original text

## Files Created
- `frontend/src/utils/piiDetector.ts` (75 lines)
- `frontend/src/components/chat/PIIDetectionBanner.vue` (25 lines)
- `frontend/src/components/chat/PIIWarningModal.vue` (70 lines)

## Files Modified
- `frontend/src/components/chat/ChatInput.vue` (integrated PII detection)
- `frontend/src/locales/en.json` — added pii section (6 keys)
- `frontend/src/locales/es.json` — added pii section (6 keys)

## Related Issues
- #495 (Agent Replay), #497 (Executive Dashboard)
