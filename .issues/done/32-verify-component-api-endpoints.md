# Issue #32: Add API Endpoint for Component Update/Delete

## Description

The CLI has `component update` and `component delete` commands but the API endpoints for these operations return incorrect status codes. Need to verify and fix.

### Requirements

- Verify `PATCH /api/v1/components/{id}` works correctly
- Verify `DELETE /api/v1/components/{id}` works correctly  
- Fix any issues with status codes (e.g., 404 for missing component should return 404 not exception)
- Add tests for both endpoints

### Technical Details

File: `src/socialseed_tasker/entrypoints/web_api/routes.py`

Current implementation wraps FileNotFoundError but should raise proper HTTPException.

### Business Value

Complete API coverage of component CRUD operations.

## STATUS: COMPLETED