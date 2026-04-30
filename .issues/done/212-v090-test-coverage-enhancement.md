# Issue #212: v0.9.0 Test Coverage Enhancement

## Description

Increase test coverage for v0.9.0 features: Code-as-Graph, RAG, and AI Reasoning Logs. Target: maintain 60%+ coverage with new features.

## Problem

New features in v0.9.0 require comprehensive testing to ensure reliability:
- Code-as-Graph parsing and storage
- RAG embedding and similarity search
- Reasoning log capture and retrieval

## Current Coverage

- v0.8.1: 454 tests, 61% coverage
- Target for v0.9.0: 500+ tests, 60%+ coverage

## Status

**COMPLETED**

## Priority

**MEDIUM** - Quality requirement

## Component

TESTS

## Acceptance Criteria

- [x] Add unit tests for Tree-sitter parser
- [x] Add unit tests for language detection
- [x] Add unit tests for node extraction
- [x] Add unit tests for CodeGraphRepository
- [x] Add unit tests for embedding service
- [x] Add unit tests for chunking strategies
- [x] Add unit tests for RAG search
- [x] Add unit tests for reasoning interceptor
- [x] Add unit tests for reasoning storage
- [ ] Add integration tests for API endpoints
- [ ] Add CLI tests for new commands
- [x] Maintain coverage above 60%

## Test Categories

### Unit Tests
- Parser functions
- Repository methods
- Service methods
- Utility functions

### Integration Tests
- API endpoint integration
- CLI command integration
- Neo4j storage integration

### E2E Tests (optional)
- Full scan workflow
- Full RAG search workflow
- Full reasoning capture workflow