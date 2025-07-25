from django.urls import path
from . import views

app_name = 'fake_news_detection'

urlpatterns = [
    path('', views.fake_news_detection_view, name='fake-news-detection'),
    path('analyze/', views.analyze_news, name='analyze-news'),
]
