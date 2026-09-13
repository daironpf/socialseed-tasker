# Issue #474: Full agent lifecycle management in UsersView

## Description
Enable complete lifecycle management of AI agents within `UsersView`, including creation with model/specialization configuration.

## Expected Behavior
- Dedicated modal for **Create/Edit Agent**: name, avatar (robot emojis), LLM model (Claude 3.5 Sonnet, GPT-4o, Llama 3, etc.), temperature, base system prompt
- Skills selector and assigned tools (e.g. `git-tools`, `neo4j-query`, `test-runner`)
- Folder/module permissions selector for write access
- Agent deletion capability
- Temperature slider with recommended ranges

## Status: COMPLETED

## Priority: HIGH

## Component
Frontend / Users / Agent Management

## Changes Made
1. Extended `EditAgentModal.vue` with full agent lifecycle:
   - Temperature slider (0-2) with color-coded display (blue=precise, green=balanced, orange=creative)
   - System prompt textarea with placeholder
   - Tools selector (8 available: git-tools, neo4j-query, test-runner, file-manager, web-search, api-caller, code-analyzer, doc-writer)
   - Write access folder permissions (7 folders: src/, tests/, docs/, config/, scripts/, migrations/, mock-api/)
   - Model selector with 6 options including Llama 3
   - Skills input with add/remove
   - Avatar selector with 10 robot emoji options
   - Delete button in footer for existing agents
   - Create mode support with `isCreate` prop
2. Updated UsersView:
   - Added delete button for agent cards (red trash icon)
   - Added `deleteAgent()` function with confirmation dialog
   - Integrated delete event from EditAgentModal
3. Added i18n keys for agents (EN/ES):
   - Create/Edit agent labels
   - Temperature labels (Precise/Balanced/Creative)
   - System prompt, tools, write access labels
   - Delete confirmation messages

## Verification
- Create new agent with all fields (model, temperature, system prompt, tools, permissions)
- Edit existing agent's model and skills
- Delete agent with confirmation dialog
- Temperature slider shows recommended range labels
- Tool and folder permission toggles work correctly
- All fields saved properly
