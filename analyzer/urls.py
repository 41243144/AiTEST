from django.urls import path
from . import views

app_name = 'analyzer'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_image, name='upload'),
    path('result/<int:pk>/', views.result, name='result'),
    path('history/', views.history, name='history'),
    path('api/analyze/', views.api_analyze, name='api_analyze'),
]