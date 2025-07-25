from django.urls import path
from . import views

app_name = 'text_ai_detection'

urlpatterns = [
    path('', views.text_ai_detection_view, name='text-ai-detection'),
    path('analyze/', views.analyze_text, name='analyze-text'),
]
