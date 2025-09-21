# apps/products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.product_delete, name='delete'),
    
    # API エンドポイント
    path('api/search/', views.product_search_api, name='search_api'),
    path('api/<int:pk>/facing-suggestion/', views.product_facing_suggestion, name='facing_suggestion'),
]