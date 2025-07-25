from django.urls import path, include
from . import views
# from .claude import ClaudeAPIView  # Temporarily commented out due to missing anthropic dependency

app_name = 'api'

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    # AI Detection Services under API
    path('ai-image-detection/', include('ai_image_detection.urls')),
    path('fake-news-detection/', include('fake_news_detection.urls')),
    # path('claude/', ClaudeAPIView.as_view(), name='claude-api'),  # Temporarily commented out
]


