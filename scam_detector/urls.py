from django.urls import path
from . import views

urlpatterns = [
    path('', views.scam_detector_view, name='scam_detector_info'),
    path('analyze/', views.analyze_scam_screenshot, name='analyze_scam_screenshot'),
]
