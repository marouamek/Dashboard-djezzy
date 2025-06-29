from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
   
    path('churn/', views.churn, name='churn'),
   
]