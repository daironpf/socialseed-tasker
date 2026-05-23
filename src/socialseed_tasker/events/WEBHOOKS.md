Webhooks and Event Bus

Overview
- WebhookManager handles subscription registry and signature verification.
- EventBus is an in-process pub/sub for internal subscribers.
- DeliveryWorker persists delivery state in StoragePort and retries with exponential backoff.

Configuration
- No new env vars required. Use existing TASKER_REDIS_URL or MemoryStorage wiring for persistence.
- DeliveryWorker parameters: max_retries, base_backoff.

Security
- Subscriptions may include a secret. Incoming webhooks are verified against subscription secrets.
- When delivering to subscribers with a secret, the payload is signed with sha256 and header X-Signature is set.

Operational notes
- Delivery state stored under keys webhook:delivery:<id> and index webhook:deliveries_index.
- DeliveryWorker can be started in-process or as a separate service.
- For high throughput, replace StoragePort with Redis and scale workers.

Testing
- Unit tests use MemoryStorage and a local HTTP server to simulate endpoints.
