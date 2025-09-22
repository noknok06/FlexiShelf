"""
商品管理ビュー
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg, Max
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import Product, Category, Manufacturer
from .forms import ProductForm, ProductSearchForm


@method_decorator(login_required, name='dispatch')
class ProductListView(ListView):
    """商品一覧ビュー"""
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related(
            'manufacturer', 'category'
        ).order_by('manufacturer__name', 'name')
        
        # 検索フィルタリング
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(jan_code__icontains=search_query) |
                Q(manufacturer__name__icontains=search_query)
            )
        
        # カテゴリフィルタ
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # メーカーフィルタ
        manufacturer_id = self.request.GET.get('manufacturer', '')
        if manufacturer_id:
            queryset = queryset.filter(manufacturer_id=manufacturer_id)
        
        # 自社/競合フィルタ
        is_own = self.request.GET.get('is_own', '')
        if is_own == 'true':
            queryset = queryset.filter(manufacturer__is_own_company=True)
        elif is_own == 'false':
            queryset = queryset.filter(manufacturer__is_own_company=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        context['categories'] = Category.objects.filter(is_active=True)
        context['manufacturers'] = Manufacturer.objects.filter(is_active=True)
        
        # 統計情報
        context['stats'] = {
            'total_products': Product.objects.filter(is_active=True).count(),
            'own_products': Product.objects.filter(is_active=True, manufacturer__is_own_company=True).count(),
            'competitor_products': Product.objects.filter(is_active=True, manufacturer__is_own_company=False).count(),
        }
        
        return context


@method_decorator(login_required, name='dispatch')
class ProductDetailView(DetailView):
    """商品詳細ビュー"""
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            'manufacturer', 'category'
        ).prefetch_related('placements__shelf', 'placements__segment')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # 配置情報
        placements = product.placements.filter(is_active=True).select_related(
            'shelf', 'segment'
        ).order_by('shelf__name', 'segment__level')
        
        context['placements'] = placements
        context['placement_count'] = placements.count()
        
        # 配置統計
        if placements.exists():
            context['placement_stats'] = {
                'total_faces': sum(p.face_count for p in placements),
                'avg_faces': placements.aggregate(avg=Avg('face_count'))['avg'],
                'shelf_count': placements.values('shelf').distinct().count(),
            }
        
        return context


@method_decorator(login_required, name='dispatch')
class ProductCreateView(CreateView):
    """商品作成ビュー"""
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'商品「{form.instance.name}」を作成しました。')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '商品作成'
        context['submit_text'] = '作成'
        return context


@method_decorator(login_required, name='dispatch')
class ProductUpdateView(UpdateView):
    """商品更新ビュー"""
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_success_url(self):
        return reverse_lazy('products:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'商品「{form.instance.name}」を更新しました。')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'商品編集 - {self.object.name}'
        context['submit_text'] = '更新'
        return context


@login_required
def product_delete(request, pk):
    """商品削除（ソフトデリート）"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    if request.method == 'POST':
        # 配置チェック
        if product.placements.filter(is_active=True).exists():
            messages.error(request, '配置中の商品は削除できません。先に配置を削除してください。')
            return redirect('products:detail', pk=pk)
        
        product.is_active = False
        product.updated_by = request.user
        product.save()
        
        messages.success(request, f'商品「{product.name}」を削除しました。')
        return redirect('products:list')
    
    return render(request, 'products/delete_confirm.html', {'product': product})


@login_required
def product_search_api(request):
    """商品検索API（Ajax用）"""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 20))
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    products = Product.objects.filter(
        is_active=True,
        name__icontains=query
    ).select_related('manufacturer')[:limit]
    
    data = {
        'products': [{
            'id': p.id,
            'name': p.name,
            'manufacturer': p.manufacturer.name,
            'width': p.width,
            'height': p.height,
            'depth': p.depth,
            'is_own': p.is_own_product,
            'image_url': p.image.url if p.image else None,
        } for p in products]
    }
    
    return JsonResponse(data)


@login_required
def product_facing_suggestion(request, pk):
    """フェーシング数の提案API"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    available_width = float(request.GET.get('width', 0))
    
    if available_width <= 0:
        return JsonResponse({'error': '有効な幅を指定してください'}, status=400)
    
    optimal_facing = product.get_optimal_facing(available_width)
    max_possible = int(available_width // product.width)
    
    data = {
        'optimal': optimal_facing,
        'max_possible': max_possible,
        'min_faces': product.min_faces,
        'max_faces': product.max_faces,
        'recommended_faces': product.recommended_faces,
        'required_width': product.width * optimal_facing,
    }
    
    return JsonResponse(data)