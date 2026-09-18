# Issue #496: Add Real-time PII & Sensitive Secrets Guardrail Warnings

## Description
Sensitive data (API keys, passwords, PII) must not leak into LLM prompts or Neo4j persistent storage. Client-side and streaming regex scanners are needed to flag potential sensitive data in chat inputs and logs.

## Expected Behavior
- Live detection banner in `ChatInput.vue` when API keys, tokens, or emails are typed
- Automated redacting (`[REDACTED_SECRET]`) in reasoning log outputs
- Warning modal blocking submission until sensitive strings are masked or confirmed

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Chat / Security

## Implementation Plan
1. Create PII/secret detection regex patterns
2. Add live detection banner to `ChatInput.vue`
3. Implement automated redacting in `MarkdownRenderer.vue`
4. Build warning modal for submission blocking
5. Add confirm/mask actions for sensitive data
6. Create security-specific types and utilities
7. Add i18n keys for security warnings
8. Integrate with existing chat and log components

## Acceptance Criteria
- [ ] Live detection in chat input
- [ ] Detection banner for API keys, tokens, emails
- [ ] Automated redacting in log outputs
- [ ] Warning modal blocking submission
- [ ] Confirm/mask actions for sensitive data
- [ ] Pattern library for common secrets
- [ ] i18n support

## Verification
- Type API key in chat input
- See detection banner appear
- Try to submit - warning modal appears
- Choose to mask - submission proceeds with redacted text
- View reasoning logs - secrets automatically redacted
- Type email - detection banner appears
- Type password - detection banner appears

## Related Issues
- #495 (Agent Replay), #497 (Executive Dashboard)
