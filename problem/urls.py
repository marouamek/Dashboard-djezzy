from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('internet/', views.problem_internet, name='problem_internet'),
    path('appel/', views.problem_appel, name='problem_appel'),
    path('offre/', views.problem_offre, name='problem_offre'),
    path('tarification/', views.problem_tarification, name='problem_tarification'),
    path('service/', views.problem_service, name='problem_service'),
    path('general/', views.problem_general, name='problem_general'),
  
]