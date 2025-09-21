"""
FlexiShelf URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# 一時的なホームページビュー
def home_view(request):
    return HttpResponse("<h1>FlexiShelf - 棚割りシステム</h1><p><a href='/admin/'>管理画面へ</a></p>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('apps.accounts.urls')),
    path('products/', include('apps.products.urls')),  # ビュー作成後に有効化
    path('shelves/', include('apps.shelves.urls')),    # ビュー作成後に有効化
    path('proposals/', include('apps.proposals.urls')), # ビュー作成後に有効化
]

# Development static/media files serving
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = 'FlexiShelf 管理'
admin.site.site_title = 'FlexiShelf'
admin.site.index_title = '棚割りシステム管理'