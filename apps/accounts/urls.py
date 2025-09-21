# apps/accounts/urls.py
from django.urls import path
from django.http import HttpResponse

app_name = 'accounts'

def temp_view(request):
    return HttpResponse("<h1>Accounts App</h1><p>ユーザー管理機能（開発中）</p>")

urlpatterns = [
    path('', temp_view, name='index'),
]