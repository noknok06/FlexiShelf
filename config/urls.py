"""
FlexiShelf URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.products.models import Product
from apps.shelves.models import Shelf, ProductPlacement


@login_required
def home_view(request):
    """ホームページビュー"""
    context = {
        'total_shelves': Shelf.objects.filter(is_active=True).count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_placements': ProductPlacement.objects.filter(is_active=True).count(),
        'recent_shelves': Shelf.objects.filter(is_active=True).order_by('-created_at')[:5],
        'recent_products': Product.objects.filter(is_active=True).order_by('-created_at')[:5],
    }
    return render(request, 'home.html', context)


def public_home_view(request):
    """未ログイン時のホームページ"""
    if request.user.is_authenticated:
        return home_view(request)
    return render(request, 'public_home.html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', public_home_view, name='home'),
    path('dashboard/', home_view, name='dashboard'),
    path('accounts/', include('apps.accounts.urls')),
    path('products/', include('apps.products.urls')),
    # path('shelves/', include('apps.shelves.urls')),
    # path('proposals/', include('apps.proposals.urls')),
]

# Development static/media files serving
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = 'FlexiShelf 管理'
admin.site.site_title = 'FlexiShelf'
admin.site.index_title = '棚割りシステム管理'