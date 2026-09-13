# Issue #474: Full agent lifecycle management in UsersView

## Description
Enable complete lifecycle management of AI agents within `UsersView`, including creation with model/specialization configuration.

## Expected Behavior
- Dedicated modal for **Create/Edit Agent**: name, avatar (robot emojis), LLM model (Claude 3.5 Sonnet, GPT-4o, Llama 3, etc.), temperature, base system prompt
- Skills selector and assigned tools (e.g. `git-tools`, `neo4j-query`, `test-runner`)
- Folder/module permissions selector for write access
- Agent deletion capability
- Temperature slider with recommended ranges

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Users / Agent Management

## Implementation Plan
1. Extend `EditAgentModal.vue` with temperature, system prompt, tool permissions
2. Add agent creation to `CreateUserModal.vue` with type toggle
3. Create `AgentPermissions.vue` component for folder/module access
4. Add agent deletion button to UsersView
5. Implement temperature slider with presets
6. Add i18n keys for agent-specific fields

## Acceptance Criteria
- [ ] Create agent with model, temperature, system prompt
- [ ] Skills and tools assignment interface
- [ ] Folder/module write permissions selector
- [ ] Agent deletion with confirmation
- [ ] Temperature slider with recommended ranges
- [ ] Validation per agent type
- [ ] i18n support

## Verification
- Create new agent with all fields configured
- Edit existing agent's model and skills
- Delete agent with confirmation
- Temperature slider shows recommended range
- Permissions correctly saved

## Related Issues
- #473 (Token metrics)
