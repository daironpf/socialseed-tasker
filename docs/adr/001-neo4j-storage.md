# ADR 001: Use Neo4j as Core Graph Storage

## Status

Accepted

## Context

SocialSeed Tasker needs a storage backend that can handle complex relationships between issues, components, and code symbols. We need to perform transitive dependency traversal and pathfinding.

## Decision

We will use Neo4j as the primary storage engine.

## Consequences

- High performance for graph traversals.
- Native support for vector indexes in recent versions.
- Requires Neo4j instance (Docker or Aura).
