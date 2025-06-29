from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('mesclients/', views.clients, name='clients'),
    path('satisfaction/', views.satisfaction, name='satisfaction'),
   
    
    
]