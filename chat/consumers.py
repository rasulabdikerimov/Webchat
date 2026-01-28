import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get('message', '')
        recipient_id = data.get('recipient_id')
        
        if not message_text or not recipient_id:
            return

        # Save message to database
        await self.save_message(message_text, recipient_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender': self.user.username,
                'sender_id': self.user.id,
                'timestamp': str(data.get('timestamp', '')),
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        sender_id = event['sender_id']
        timestamp = event['timestamp']
        
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'sender_id': sender_id,
            'timestamp': timestamp,
        }))

    @database_sync_to_async
    def save_message(self, message_text, recipient_id):
        try:
            recipient = User.objects.get(id=recipient_id)
            Message.objects.create(
                sender=self.user,
                recipient=recipient,
                text=message_text
            )
        except User.DoesNotExist:
            pass
