from socialseed_tasker.events.bus import EventBus
from socialseed_tasker.events.serializers import EventDTO

def test_bus_publish_subscribe():
    bus = EventBus()
    received = []
    def handler(e):
        received.append(e.type)
    bus.subscribe("my.event", handler)
    e = EventDTO(id="1", type="my.event", source="s", payload={}, created_at="t")
    bus.publish(e)
    assert "my.event" in received
