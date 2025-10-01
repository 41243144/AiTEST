from django.urls import path
from . import views

app_name = 'analyzer'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_image, name='upload'),
    path('result/<int:pk>/', views.result, name='result'),
    path('history/', views.history, name='history'),
    path('generate-story/<int:pk>/', views.generate_story, name='generate_story'),
    path('api/analyze/', views.api_analyze, name='api_analyze'),
    path('api/generate-story/', views.api_generate_story, name='api_generate_story'),
]