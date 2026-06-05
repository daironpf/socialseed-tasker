# Issue #406: Empty batch request returns 201 instead of 400

## Description
`POST /api/v1/issues/batch` with an empty `issues: []` array returns HTTP 201 with `successful=0, failed=0`. This is semantically questionable — a request with zero items should either return 400 (bad request) or at minimum be documented as accepted behavior.

## Expected Behavior
- Option A: Return 400 with `{"error": "No issues provided"}`.
- Option B: Return 201 but document that empty batches are accepted as no-ops.

## Actual Behavior
```json
{
  "data": {
    "total_requested": 0,
    "successful": 0,
    "failed": 0,
    "results": []
  }
}
```
HTTP 201 Created.

## Steps to Reproduce
```bash
curl -X POST http://localhost:8888/api/v1/issues/batch \
  -H "Content-Type: application/json" \
  -d '{"issues": []}'
```

## Status: PENDING

## Priority: LOW

## Component
API / Issues / Batch

## Suggested Fix
Add a guard at the top of `create_issues_batch()`:
```python
if not body.issues:
    raise HTTPException(status_code=400, detail="No issues provided")
```

## Impact
- Low: empty batch is harmless but violates the principle of least astonishment.
