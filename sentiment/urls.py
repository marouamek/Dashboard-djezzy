from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('sentiment_client/', views.sentiment_client, name='sentiment_client'),
]