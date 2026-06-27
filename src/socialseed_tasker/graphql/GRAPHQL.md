GraphQL API Guide

Overview
- Schema-first GraphQL API using ariadne.
- Endpoints:
  - HTTP queries and mutations: POST /graphql
  - WebSocket subscriptions: /graphql/ws

Authentication and RBAC
- Provide Authorization: Bearer <token> header.
- Resolvers enforce RBAC using container.rbac.has_permission with same permission names as CLI/API.

Schema
- The SDL is located at graphql/schema.graphql.
- Exported SDL is written to graphql/schema_export.graphql when TASKER_EXPORT_GRAPHQL=1.

Running
- Start service:
  docker compose -f compose/tools/graphql.yml up -d --build
- Local dev:
  TASKER_EXPORT_GRAPHQL=1 python -m socialseed_tasker.graphql.server

Examples
- Query issue:
  { issue(id: "i1") { id title status } }
- Mutation createIssue:
  mutation { createIssue(id:"i1", title:"T") { id title } }
- Subscription (client must use GraphQL WS protocol):
  subscription { issueEvents(issueId: "i1") { id type payload } }
