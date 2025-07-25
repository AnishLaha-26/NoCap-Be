from rest_framework import serializers
from .models import ClaudeConversation, ClaudeMessage, ClaudeAPIUsage


class ClaudeMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaudeMessage
        fields = ['id', 'role', 'content', 'model_used', 'tokens_used', 'created_at']


class ClaudeConversationSerializer(serializers.ModelSerializer):
    messages = ClaudeMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ClaudeConversation
        fields = ['id', 'session_id', 'title', 'created_at', 'updated_at', 'messages', 'message_count']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class ClaudeAPIUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaudeAPIUsage
        fields = ['id', 'model_used', 'input_tokens', 'output_tokens', 'total_tokens', 
                 'estimated_cost', 'request_timestamp']
