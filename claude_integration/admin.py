from django.contrib import admin
from .models import ClaudeConversation, ClaudeMessage, ClaudeAPIUsage


@admin.register(ClaudeConversation)
class ClaudeConversationAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'title', 'user', 'created_at', 'updated_at', 'message_count']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['session_id', 'title', 'user__username']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(ClaudeMessage)
class ClaudeMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'content_preview', 'model_used', 'tokens_used', 'created_at']
    list_filter = ['role', 'model_used', 'created_at']
    search_fields = ['content', 'conversation__session_id']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(ClaudeAPIUsage)
class ClaudeAPIUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'model_used', 'total_tokens', 'estimated_cost', 'request_timestamp']
    list_filter = ['model_used', 'request_timestamp']
    search_fields = ['user__username', 'model_used']
    readonly_fields = ['request_timestamp']
