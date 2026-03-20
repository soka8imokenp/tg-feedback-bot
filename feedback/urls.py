from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='feedback_index'),
    path('submit/', views.submit_feedback, name='submit_feedback'),
]