# Issue #64: Add API endpoint to create multiple dependencies at once

## Description

Creating the dependency graph for a project requires one HTTP request per dependency relationship. For the shoe ecommerce project with 11 dependencies, this meant 11 separate curl commands. A bulk endpoint would significantly improve the developer experience.

## Problem Found

Setting up the ecommerce dependency graph required 11 individual POST requests:
```
POST /issues/{id}/dependencies {"depends_on_id": "..."}
POST /issues/{id}/dependencies {"depends_on_id": "..."}
...
```

## Impact

- Tedious for projects with many interdependent issues
- Scripting the setup requires error handling for each individual request
- No atomicity - if request 7 fails, the first 6 are already created

## Suggested Fix

- Add `POST /api/v1/issues/{id}/dependencies/bulk` accepting `{"depends_on_ids": ["uuid1", "uuid2", ...]}`
- Wrap in a Neo4j transaction for atomicity
- Return list of created dependencies with individual status codes
- Add circular dependency detection that validates the entire batch

## Priority

LOW

## Labels

api, enhancement, dx
