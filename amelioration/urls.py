from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('internet/', views.amelioration_internet, name='amelioration_internet'),
    path('appel/', views.amelioration_appel, name='amelioration_appel'),
    path('offre/', views.amelioration_offre, name='amelioration_offre'),
    path('tarification/', views.amelioration_tarification, name='amelioration_tarification'),
    path('service/', views.amelioration_service, name='amelioration_service'),
    path('home/', views.amelioration_home, name='amelioration_home'),
  
]