from django.db import models
from baseapp.models import BaseModel


class Conversation(BaseModel):
    is_group = models.BooleanField(default=False)
    name = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.name or str(self.pk)
    

class ConversationParticipant(BaseModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, related_name='conversations')
    
    class Meta:
        unique_together = ['conversation', 'user']
        
class Message(BaseModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField(blank=True)
    file = models.FileField(upload_to="chat_attachments/", null=True, blank=True)
    reply_to = models.ForeignKey('chat.Message', on_delete=models.SET_NULL, null=True, blank=True,  related_name='replies')
    forward = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.sender} - {self.content}"   
    
    
class UnreadMessage(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="unread_for")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="unread_messages")
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name="unread_messages")

    class Meta:
        unique_together = ["message", "user"]
        indexes = [
            models.Index(fields=["conversation", "user"]),
        ]

    def __str__(self):
        return f"{self.user} unread {self.message_id}"
    
    
    