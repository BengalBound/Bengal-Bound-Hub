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
        
        agent = SereaAgent.objects.get(id=self.agent_id)
        
        # Create user message
        client_msg = ConversationMessage.objects.create(
            agent=agent,
            sender=self.user.email,
            message_text=message_text,
        )
        
        # Broadcast user message back so other clients connected see it immediately
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        
        payload = {
            'id': client_msg.id,
            'sender': client_msg.sender,
            'text': client_msg.message_text,
            'is_permission_request': client_msg.is_permission_request,
            'permission_granted': client_msg.permission_granted,
            'created_at': client_msg.created_at.isoformat(),
        }
        
        # Using async_to_sync since this runs in sync thread via database_sync_to_async
        async_to_sync(channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': payload
            }
        )
        
        # Dispatch Celery Task for Serea's reply
        process_chat_message_task.delay(agent.id, message_text, self.user.email)
