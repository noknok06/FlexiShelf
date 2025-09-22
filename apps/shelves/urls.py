# apps/shelves/urls.py
from django.urls import path
from . import views

app_name = 'shelves'

urlpatterns = [
    path('', views.ShelfListView.as_view(), name='list'),
    path('create/', views.ShelfCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ShelfDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ShelfUpdateView.as_view(), name='update'),
    path('<int:pk>/edit/', views.ShelfEditView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.shelf_delete, name='delete'),
    
    # API エンドポイント
    path('api/placement/create/', views.placement_create_api, name='placement_create_api'),
    path('api/placement/<int:placement_id>/update/', views.placement_update_api, name='placement_update_api'),
    path('api/placement/<int:placement_id>/delete/', views.placement_delete_api, name='placement_delete_api'),
    path('api/segment/<int:segment_id>/height/', views.segment_height_update_api, name='segment_height_update_api'),
    path('api/placement/validate/', views.placement_validation_api, name='placement_validation_api'),
]