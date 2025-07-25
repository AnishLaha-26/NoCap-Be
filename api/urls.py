from django.urls import path
from . import views
from .claude import ClaudeAPIView

app_name = 'api'

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('claude/', ClaudeAPIView.as_view(), name='claude-api'),
]
