from django.urls import path
from django.views.decorators.http import require_http_methods
from . import views

app_name = 'fake_news_detection'

urlpatterns = [
    path('', views.fake_news_detection_view, name='fake-news-detection'),
    path('analyze/', require_http_methods(['POST'])(views.analyze_news), name='analyze-news'),
]
