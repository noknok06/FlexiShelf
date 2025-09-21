# apps/proposals/urls.py
from django.urls import path
from django.http import HttpResponse

app_name = 'proposals'

def temp_view(request):
    return HttpResponse("<h1>Proposals App</h1><p>提案機能（開発中）</p>")

urlpatterns = [
    path('', temp_view, name='index'),
]