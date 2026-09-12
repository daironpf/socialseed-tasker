# Issue #462: Policy edit form silently drops rule and level changes

## Description
The edit policy modal in `PoliciesView.vue` presents `rule` and `level` fields for editing, but `submitEdit()` never includes them in the update payload. Changes to these fields are silently discarded every time.

The edit form maps `policy.rules?.[0]?.type` to `editForm.rule` and `policy.rules?.[0]?.severity` to `editForm.level`, but these values are never included in the save payload. The mock server's PATCH endpoint only updates fields that are sent, so the old `rule`/`level` values persist.

## Status: TODO

## Priority: HIGH

## Component
Frontend / PoliciesView

## Acceptance Criteria
1. Add `rule` and `level` to the `submitEdit()` payload in `PoliciesView.vue`
2. Verify that changes to rule and level are persisted after save
3. `npm run build` passes

## Related Issues
- None
