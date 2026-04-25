# Issue #82: Active Policy Enforcement

## Description

Implement blocking of API/CLI writes if they violate defined Architectural Rules (forbidden technologies, depth limits, forbidden dependencies). The architectural rules module exists in `core/project_analysis/` but is not yet enforced at API/CLI level.

## Requirements

- Integrate ArchitecturalRulesAnalyzer with API write operations (POST/PUT/PATCH)
- Integrate with CLI create/update commands
- Return validation errors with clear messages when rules are violated
- Support configurable enforcement modes: "warn", "block", "disabled"
- Add rule violation details in response (which rule, why, suggested fix)

## Technical Details

### Configuration
- `TASKER_POLICY_ENFORCEMENT_MODE` - "warn", "block", or "disabled" (default: "warn")

### API Changes
- Add middleware to validate writes against rules
- Create `/policies/validate` endpoint to check rules without writing
- Add `X-Policy-Enforcement` header override for clients

### CLI Changes
- Add `--enforce` flag to create/update commands
- Show policy warnings before confirmations
- Block execution when in "block" mode

## Business Value

Prevents agents from introducing technical debt by enforcing architectural constraints at write time, rather than detecting violations later.

## Status: COMPLETED