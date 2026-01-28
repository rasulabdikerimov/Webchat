import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # Use conversation prefix to match the group we'll send to
        self.room_group_name = f'conversation_{self.room_name}'

        logger.info(f"User {self.user.username} connecting to room {self.room_group_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"User {self.user.username} connected to room {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user.username} disconnected from room {self.room_group_name}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_text = data.get('message', '')
            recipient_id = data.get('recipient_id')
            
            if not message_text or not recipient_id:
                return

            recipient = await self.get_user(recipient_id)
            if not recipient:
                return

            # Save message to database
            await self.save_message(message_text, recipient_id)

            logger.info(f"Message from {self.user.username} to {recipient.username} in room {self.room_group_name}")

            # Send to both users in this conversation (already in the right group)
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
        except Exception as e:
            logger.error(f"Error in receive: {e}")

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

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
