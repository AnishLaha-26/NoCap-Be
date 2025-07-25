from django.db import models
from django.contrib.auth.models import User


class ClaudeConversation(models.Model):
    """
    Model to store Claude conversation history
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.session_id} - {self.title or 'Untitled'}"


class ClaudeMessage(models.Model):
    """
    Model to store individual messages in a Claude conversation
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(ClaudeConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    model_used = models.CharField(max_length=100, default='claude-3-5-sonnet-20240620')
    tokens_used = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ClaudeAPIUsage(models.Model):
    """
    Model to track Claude API usage and costs
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    model_used = models.CharField(max_length=100)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    request_timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-request_timestamp']
    
    def __str__(self):
        return f"API Usage - {self.model_used} - {self.total_tokens} tokens"
