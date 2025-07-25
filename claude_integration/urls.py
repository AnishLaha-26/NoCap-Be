from django.urls import path
from . import views

app_name = 'claude_integration'

urlpatterns = [
    path('chat/', views.ClaudeAPIView.as_view(), name='claude-chat'),
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<str:session_id>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
]
