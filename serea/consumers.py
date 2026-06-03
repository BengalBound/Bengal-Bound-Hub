import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

class SereaChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.agent_id = self.scope['url_route']['kwargs']['agent_id']
        self.room_group_name = f'agent_{self.agent_id}'
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        # Ensure user has access to this agent
        has_access = await self.check_tenant_access()
        if not has_access:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket (from the client)
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        
        if not message:
            return

        # Handle incoming message via Celery
        await self.process_chat_message(message)

    # Receive message from room group (broadcast from Celery/Signals)
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def check_tenant_access(self):
        from .models import SereaAgent
        try:
            agent = SereaAgent.objects.get(id=self.agent_id)
            if self.user.is_workspace_user:
                return True
            return agent.tenant == self.user
        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def process_chat_message(self, message_text):
        from .models import SereaAgent, ConversationMessage
        from .tasks import process_chat_message_task

        try:
            agent = SereaAgent.objects.get(id=self.agent_id)
        except SereaAgent.DoesNotExist:
            return

        # Saving triggers the post_save signal in signals.py which broadcasts to the group.
        ConversationMessage.objects.create(
            agent=agent,
            sender=self.user.email,
            message_text=message_text,
        )

        process_chat_message_task.delay(agent.id, message_text, self.user.email)
