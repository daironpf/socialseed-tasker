# Issue #487: Add agent creation mode to CreateUserModal

## Description
Extend the user creation form to allow fluid switching between account types (`human` vs `agent`).

## Expected Behavior
- Tab/selector in modal: **Human** vs **AI Agent**
- If **Agent** selected: enable Model selector, Specialization, Robot avatar picker
- Different form fields based on type selection
- Different validation schemas per user type
- Model options: Claude 3.5 Sonnet, GPT-4 Turbo, GPT-4o, Claude 3 Opus, Gemini Pro, Llama 3
- Robot avatar picker (8 tech/robot emojis)

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Users / Create Agent

## Implementation Plan
1. Add type toggle (Human/Agent) to CreateUserModal
2. Conditionally show agent-specific fields (model, specialization, robot avatar)
3. Implement different validation schemas per type
4. Add model selector dropdown
5. Add robot avatar picker
6. Submit with correct `type` field
7. Add i18n keys for agent fields

## Acceptance Criteria
- [ ] Type toggle: Human vs AI Agent
- [ ] Agent fields: Model, Specialization, Robot avatar
- [ ] Different validation per type
- [ ] Model selector with all options
- [ ] Robot avatar picker (8 emojis)
- [ ] Correct type sent to API
- [ ] i18n support

## Verification
- Open CreateUserModal
- Toggle to Agent type
- Agent-specific fields appear
- Fill required agent fields
- Submit creates agent with correct type
- Toggle back to Human - agent fields hidden

## Related Issues
- #486 (Bulk actions)
