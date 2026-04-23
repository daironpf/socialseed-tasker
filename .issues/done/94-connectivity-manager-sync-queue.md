# Issue #94: ConnectivityManager & SyncQueue

## Description

Implement offline-first "Guard" that queues agent actions during power/internet outages and flushes them to the cloud upon reconnection. This is the infrastructure for the offline-first sync engine.

## Requirements

- Create ConnectivityManager class to monitor network status
- Implement connection state machine: online, offline, reconnecting
- Add automatic reconnection detection with exponential backoff
- Implement queue flushing on reconnection
- Add priority queue (critical operations first)
- Handle partial failures (retry failed items only)
- Add metrics: queue size, sync latency, failure rate

## Technical Details

### ConnectivityManager
```python
class ConnectivityManager:
    def is_online() -> bool: ...
    def on_connect(callback): ...
    def on_disconnect(callback): ...
    def get_latency() -> float: ...
```

### Queue Priority
- Critical: Issue creation, status changes
- Normal: Label changes, comments
- Low: Metadata updates

### Metrics Endpoint
- `GET /system/connectivity` - Network status
- `GET /system/sync/metrics` - Queue and sync metrics

## Business Value

Ensures reliable sync even with unstable connectivity. Agents can operate continuously without losing work.

## Status: COMPLETED