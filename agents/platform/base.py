class BaseAgentAdapter:
    def __init__(self, instance):
        self.instance = instance

    def send_notification(self, title: str, message: str, urgency: str = 'normal') -> bool:
        raise NotImplementedError

    def push_event(self, event_type: str, payload: dict) -> bool:
        raise NotImplementedError

    def test_connection(self) -> bool:
        raise NotImplementedError
