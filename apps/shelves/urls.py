# apps/shelves/urls.py
from django.urls import path
from django.http import HttpResponse

app_name = 'shelves'

def temp_view(request):
    return HttpResponse("<h1>Shelves App</h1><p>棚割り機能（開発中）</p>")

urlpatterns = [
    path('', temp_view, name='index'),
]
