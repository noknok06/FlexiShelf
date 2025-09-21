# apps/shelves/urls.py
from django.urls import path
from . import views

app_name = 'shelves'

urlpatterns = [
    path('', views.ShelfListView.as_view(), name='list'),
    path('create/', views.ShelfCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ShelfDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ShelfUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.shelf_delete, name='delete'),
    
    # API エンドポイント
    path('api/placement/create/', views.placement_create_api, name='placement_create_api'),
    path('api/placement/<int:placement_id>/delete/', views.placement_delete_api, name='placement_delete_api'),
]