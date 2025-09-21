# apps/proposals/urls.py
from django.urls import path
from django.http import HttpResponse
from . import views


app_name = 'proposals'

urlpatterns = [
    path('', views.ProposalListView.as_view(), name='list'),
    
]