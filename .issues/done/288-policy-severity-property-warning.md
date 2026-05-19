# Issue #288: Policy Node Severity Property Warning

## Description
When creating or updating Policy nodes in Neo4j, a warning is logged indicating that the `severity` property does not exist on the Policy node schema. This is a schema alignment issue where the code attempts to set a `severity` property that is not defined in the Policy node type.

## Expected Behavior
- No warnings when creating Policy nodes
- Policy node schema should be clearly defined
- Properties should match the schema

## Actual Behavior
```
Warning: Property 'severity' does not exist on node 'Policy'
```

## Technical Analysis

### Problem Location
- Policy nodes are created via API routes
- The Policy entity or repository code sets `severity` property
- Neo4j schema validation warns about undefined property

### Root Cause
The Policy entity in `core/` layer or repository code is setting a `severity` property that is not defined in the Neo4j schema for Policy nodes.

### Affected Code Areas
- Policy entity definition
- Policy repository write operations
- Policy creation API endpoint

## Steps to Reproduce
1. Start Tasker services
2. Create a Policy via API or CLI
3. Check Neo4j logs or application logs
4. Observe warning about `severity` property

## Component
Storage - Neo4j Graph Schema

## Status: TODO

## Priority: MEDIUM

## Technical Implementation

### Option 1: Add Severity to Schema
If `severity` is a valid property, add it to the Neo4j schema with proper index.

### Option 2: Remove Severity from Code
If `severity` is not needed, remove it from the Policy creation/update code.

### Option 3: Document Severity Usage
If severity is optional or for future use, add to schema with NULL default.

## Acceptance Criteria
- [ ] No Neo4j warnings about Policy node properties
- [ ] Policy schema is documented and consistent
- [ ] Severity property is either defined or removed from code

## Impact
- **Low**: Warning does not block functionality
- **UX**: Clutters logs with warnings
- **Maintenance**: Schema inconsistency can cause confusion

## Related Issues
- Issue #287: Agent Registration INTERNAL_ERROR (separate but similar parameter/schema issue)