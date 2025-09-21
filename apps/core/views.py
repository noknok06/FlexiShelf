# apps/core/views.py
"""
コア機能ビュー
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_api(request):
    """ダッシュボード用API"""
    from apps.products.models import Product
    from apps.shelves.models import Shelf, ProductPlacement
    
    data = {
        'stats': {
            'total_products': Product.objects.filter(is_active=True).count(),
            'total_shelves': Shelf.objects.filter(is_active=True).count(),
            'total_placements': ProductPlacement.objects.filter(is_active=True).count(),
            'own_products': Product.objects.filter(
                is_active=True, 
                manufacturer__is_own_company=True
            ).count(),
        }
    }
    
    return JsonResponse(data)

