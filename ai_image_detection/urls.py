from django.urls import path
from . import views

app_name = 'ai_image_detection'

urlpatterns = [
    path('', views.ai_image_detection_view, name='ai-image-detection'),
    path('analyze/', views.analyze_image, name='analyze-image'),
    path('analyze_ai/', views.analyze_image_ai, name='analyze-image-ai'),
]
