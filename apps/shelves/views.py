"""
棚管理ビュー
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg, Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from .models import Shelf, ShelfSegment, ProductPlacement
from .forms import ShelfForm, ShelfSegmentFormSet, ProductPlacementForm
from apps.products.models import Product


@method_decorator(login_required, name='dispatch')
class ShelfListView(ListView):
    """棚一覧ビュー"""
    model = Shelf
    template_name = 'shelves/list.html'
    context_object_name = 'shelves'
    paginate_by = 12

    def get_queryset(self):
        queryset = Shelf.objects.filter(is_active=True).prefetch_related(
            'segments',
            Prefetch('placements', queryset=ProductPlacement.objects.filter(is_active=True))
        ).annotate(
            segment_count=Count('segments', filter=Q(segments__is_active=True)),
            placement_count=Count('placements', filter=Q(placements__is_active=True))
        ).order_by('name')
        
        # 検索フィルタリング
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 統計情報
        context['stats'] = {
            'total_shelves': Shelf.objects.filter(is_active=True).count(),
            'total_segments': ShelfSegment.objects.filter(is_active=True).count(),
            'total_placements': ProductPlacement.objects.filter(is_active=True).count(),
        }
        
        return context


@method_decorator(login_required, name='dispatch')
class ShelfDetailView(DetailView):
    """棚詳細ビュー"""
    model = Shelf
    template_name = 'shelves/detail.html'
    context_object_name = 'shelf'

    def get_queryset(self):
        return Shelf.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'segments',
                queryset=ShelfSegment.objects.filter(is_active=True).prefetch_related(
                    Prefetch(
                        'placements',
                        queryset=ProductPlacement.objects.filter(is_active=True).select_related('product__manufacturer')
                    )
                ).order_by('level')
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shelf = self.object
        
        # 段ごとの配置情報を整理
        segments_data = []
        for segment in shelf.segments.all():
            placements = list(segment.placements.all())
            segments_data.append({
                'segment': segment,
                'placements': placements,
                'utilization': (sum(p.occupied_width for p in placements) / shelf.width * 100) if placements else 0,
                'available_width': segment.available_width,
            })
        
        context['segments_data'] = segments_data
        
        # 統計情報
        all_placements = ProductPlacement.objects.filter(shelf=shelf, is_active=True)
        if all_placements.exists():
            context['shelf_stats'] = {
                'total_products': all_placements.count(),
                'total_faces': all_placements.aggregate(total=Sum('face_count'))['total'],
                'avg_utilization': sum(data['utilization'] for data in segments_data) / len(segments_data) if segments_data else 0,
                'own_products': all_placements.filter(product__manufacturer__is_own_company=True).count(),
                'competitor_products': all_placements.filter(product__manufacturer__is_own_company=False).count(),
            }
        
        return context


@method_decorator(login_required, name='dispatch')
class ShelfCreateView(CreateView):
    """棚作成ビュー"""
    model = Shelf
    form_class = ShelfForm
    template_name = 'shelves/form.html'
    success_url = reverse_lazy('shelves:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '棚作成'
        context['submit_text'] = '作成'
        
        # セグメントフォームセット
        if self.request.POST:
            context['segment_formset'] = ShelfSegmentFormSet(self.request.POST, prefix='segments')
        else:
            context['segment_formset'] = ShelfSegmentFormSet(prefix='segments')
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        segment_formset = context['segment_formset']
        
        form.instance.created_by = self.request.user
        
        if segment_formset.is_valid():
            self.object = form.save()
            segment_formset.instance = self.object
            segment_formset.save()
            
            messages.success(self.request, f'棚「{self.object.name}」を作成しました。')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


@method_decorator(login_required, name='dispatch')
class ShelfUpdateView(UpdateView):
    """棚更新ビュー"""
    model = Shelf
    form_class = ShelfForm
    template_name = 'shelves/form.html'

    def get_queryset(self):
        return Shelf.objects.filter(is_active=True)

    def get_success_url(self):
        return reverse_lazy('shelves:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'棚編集 - {self.object.name}'
        context['submit_text'] = '更新'
        
        # セグメントフォームセット
        if self.request.POST:
            context['segment_formset'] = ShelfSegmentFormSet(
                self.request.POST, 
                instance=self.object,
                prefix='segments'
            )
        else:
            context['segment_formset'] = ShelfSegmentFormSet(
                instance=self.object,
                prefix='segments'
            )
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        segment_formset = context['segment_formset']
        
        form.instance.updated_by = self.request.user
        
        if segment_formset.is_valid():
            self.object = form.save()
            segment_formset.save()
            
            messages.success(self.request, f'棚「{self.object.name}」を更新しました。')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


@login_required
def shelf_delete(request, pk):
    """棚削除（ソフトデリート）"""
    shelf = get_object_or_404(Shelf, pk=pk, is_active=True)
    
    if request.method == 'POST':
        # 配置チェック
        if shelf.placements.filter(is_active=True).exists():
            messages.error(request, '商品が配置されている棚は削除できません。先に配置を削除してください。')
            return redirect('shelves:detail', pk=pk)
        
        shelf.is_active = False
        shelf.updated_by = request.user
        shelf.save()
        
        # 関連する段も無効化
        shelf.segments.update(is_active=False)
        
        messages.success(request, f'棚「{shelf.name}」を削除しました。')
        return redirect('shelves:list')
    
    return render(request, 'shelves/delete_confirm.html', {'shelf': shelf})


@method_decorator(login_required, name='dispatch')
class ShelfEditView(DetailView):
    """棚割り編集ビュー"""
    model = Shelf
    template_name = 'shelves/edit.html'
    context_object_name = 'shelf'

    def get_queryset(self):
        return Shelf.objects.filter(is_active=True).prefetch_related(
            'segments__placements__product__manufacturer'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 商品検索用のクエリセット
        context['products'] = Product.objects.filter(is_active=True).select_related(
            'manufacturer', 'category'
        ).order_by('manufacturer__name', 'name')
        
        # 段データをJSON形式で提供
        segments_data = []
        for segment in self.object.segments.filter(is_active=True).order_by('level'):
            placements_data = []
            for placement in segment.placements.filter(is_active=True).order_by('x_position'):
                placements_data.append({
                    'id': placement.id,
                    'product_id': placement.product.id,
                    'product_name': placement.product.name,
                    'manufacturer_name': placement.product.manufacturer.name,
                    'is_own': placement.product.is_own_product,
                    'x_position': placement.x_position,
                    'face_count': placement.face_count,
                    'occupied_width': placement.occupied_width,
                    'product_width': placement.product.width,
                    'product_height': placement.product.height,
                })
            
            segments_data.append({
                'id': segment.id,
                'level': segment.level,
                'height': segment.height,
                'y_position': segment.y_position,
                'available_width': segment.available_width,
                'placements': placements_data,
            })
        
        context['segments_json'] = segments_data
        
        return context


# API ビュー

@login_required
@require_http_methods(["POST"])
def placement_create_api(request):
    """商品配置API"""
    try:
        shelf_id = request.POST.get('shelf_id')
        segment_id = request.POST.get('segment_id')
        product_id = request.POST.get('product_id')
        x_position = float(request.POST.get('x_position', 0))
        face_count = int(request.POST.get('face_count', 1))
        
        shelf = get_object_or_404(Shelf, id=shelf_id, is_active=True)
        segment = get_object_or_404(ShelfSegment, id=segment_id, shelf=shelf, is_active=True)
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # 新しい配置を作成
        placement = ProductPlacement(
            shelf=shelf,
            segment=segment,
            product=product,
            x_position=x_position,
            face_count=face_count,
            created_by=request.user
        )
        
        # バリデーション
        placement.full_clean()
        placement.save()
        
        return JsonResponse({
            'success': True,
            'placement': {
                'id': placement.id,
                'x_position': placement.x_position,
                'face_count': placement.face_count,
                'occupied_width': placement.occupied_width,
                'end_position': placement.end_position,
            }
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'errors': e.message_dict if hasattr(e, 'message_dict') else [str(e)]
        }, status=400)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'errors': ['入力値が正しくありません']
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': [str(e)]
        }, status=500)


@login_required
@require_http_methods(["POST"])
def placement_update_api(request, placement_id):
    """商品配置更新API"""
    try:
        placement = get_object_or_404(
            ProductPlacement, 
            id=placement_id, 
            is_active=True
        )
        
        # 更新可能なフィールド
        if 'x_position' in request.POST:
            placement.x_position = float(request.POST['x_position'])
        
        if 'face_count' in request.POST:
            placement.face_count = int(request.POST['face_count'])
        
        placement.updated_by = request.user
        
        # バリデーション
        placement.full_clean()
        placement.save()
        
        return JsonResponse({
            'success': True,
            'placement': {
                'id': placement.id,
                'x_position': placement.x_position,
                'face_count': placement.face_count,
                'occupied_width': placement.occupied_width,
                'end_position': placement.end_position,
            }
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'errors': e.message_dict if hasattr(e, 'message_dict') else [str(e)]
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': [str(e)]
        }, status=500)


@login_required
@require_http_methods(["POST"])
def placement_delete_api(request, placement_id):
    """商品配置削除API"""
    try:
        placement = get_object_or_404(
            ProductPlacement, 
            id=placement_id, 
            is_active=True
        )
        
        placement.is_active = False
        placement.updated_by = request.user
        placement.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': [str(e)]
        }, status=500)


@login_required
def segment_height_update_api(request, segment_id):
    """段高さ更新API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'errors': ['POSTメソッドが必要です']}, status=405)
    
    try:
        segment = get_object_or_404(ShelfSegment, id=segment_id, is_active=True)
        new_height = float(request.POST.get('height', 0))
        
        if new_height <= 0:
            return JsonResponse({
                'success': False,
                'errors': ['高さは0より大きい値である必要があります']
            }, status=400)
        
        # 配置されている商品の高さチェック
        max_product_height = segment.placements.filter(is_active=True).aggregate(
            max_height=Max('product__height')
        )['max_height']
        
        if max_product_height and new_height < max_product_height:
            return JsonResponse({
                'success': False,
                'errors': [f'配置されている商品の最大高さ（{max_product_height}cm）より小さくできません']
            }, status=400)
        
        segment.height = new_height
        segment.updated_by = request.user
        segment.save()
        
        return JsonResponse({
            'success': True,
            'segment': {
                'id': segment.id,
                'height': segment.height,
                'y_position': segment.y_position,
            }
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'errors': ['高さの値が正しくありません']
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': [str(e)]
        }, status=500)


@login_required
def placement_validation_api(request):
    """配置バリデーションAPI"""
    try:
        segment_id = request.GET.get('segment_id')
        product_id = request.GET.get('product_id')
        x_position = float(request.GET.get('x_position', 0))
        face_count = int(request.GET.get('face_count', 1))
        placement_id = request.GET.get('placement_id')  # 更新時
        
        segment = get_object_or_404(ShelfSegment, id=segment_id, is_active=True)
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # 一時的な配置オブジェクトを作成してバリデーション
        temp_placement = ProductPlacement(
            shelf=segment.shelf,
            segment=segment,
            product=product,
            x_position=x_position,
            face_count=face_count
        )
        
        # 既存配置の除外（更新時）
        if placement_id:
            temp_placement.pk = int(placement_id)
        
        # バリデーション実行
        temp_placement.full_clean()
        
        return JsonResponse({
            'valid': True,
            'required_width': product.width * face_count,
            'end_position': x_position + (product.width * face_count),
            'available_width': segment.available_width,
        })
        
    except ValidationError as e:
        return JsonResponse({
            'valid': False,
            'errors': e.message_dict if hasattr(e, 'message_dict') else [str(e)]
        })
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'errors': [str(e)]
        })