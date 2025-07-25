from django.urls import path
from . import views

app_name = 'deepfake_detection'

urlpatterns = [
    path('', views.deepfake_detection_view, name='deepfake-detection'),
    path('analyze/', views.analyze_deepfake, name='analyze-deepfake'),
]
