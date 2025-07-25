"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include('api.urls')),
    # path('claude/', include('claude_integration.urls')),  # Temporarily commented out - app doesn't exist
    
    # AI Detection Services
    path('text-ai-detection/', include('text_ai_detection.urls')),
    path('fake-news-detection/', include('fake_news_detection.urls')),
    path('ai-image-detection/', include('ai_image_detection.urls')),
    path('deepfake-detection/', include('deepfake_detection.urls')),
    
    # DRF's browsable API auth
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa