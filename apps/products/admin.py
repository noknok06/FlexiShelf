"""
商品管理画面
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Manufacturer, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'sort_order', 'product_count', 'is_active']
    list_filter = ['parent', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sort_order', 'name']
    list_editable = ['sort_order', 'is_active']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'code', 'parent')
        }),
        ('表示設定', {
            'fields': ('sort_order',),
        }),
    )
    
    def product_count(self, obj):
        """カテゴリ内の商品数"""
        return obj.products.filter(is_active=True).count()
    product_count.short_description = '商品数'


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_own_company', 'product_count', 'is_active']
    list_filter = ['is_own_company', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['name']
    list_editable = ['is_own_company', 'is_active']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'code')
        }),
        ('区分', {
            'fields': ('is_own_company',),
        }),
    )
    
    def product_count(self, obj):
        """メーカーの商品数"""
        return obj.products.filter(is_active=True).count()
    product_count.short_description = '商品数'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'jan_code', 'manufacturer', 'category', 
        'dimensions_display', 'facing_display', 'price_display',
        'placement_count', 'is_own_product', 'is_active'
    ]
    list_filter = [
        'manufacturer', 'category', 'size_category', 
        'manufacturer__is_own_company', 'is_active'
    ]
    search_fields = ['name', 'jan_code', 'manufacturer__name', 'category__name']
    ordering = ['manufacturer__name', 'name']
    list_editable = ['is_active']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'jan_code', 'manufacturer', 'category', 'description')
        }),
        ('物理寸法', {
            'fields': ('width', 'height', 'depth', 'size_category'),
            'description': '実際の商品サイズをcm単位で入力してください。'
        }),
        ('フェーシング設定', {
            'fields': ('min_faces', 'recommended_faces', 'max_faces'),
            'description': '棚での配置時のフェース数制約を設定してください。'
        }),
        ('その他', {
            'fields': ('price', 'image'),
        }),
    )
    
    readonly_fields = ['volume_display', 'recommended_width_display']
    
    def dimensions_display(self, obj):
        """寸法表示"""
        return f"{obj.width}×{obj.height}×{obj.depth}cm"
    dimensions_display.short_description = '寸法(W×H×D)'
    
    def facing_display(self, obj):
        """フェーシング表示"""
        return f"{obj.min_faces}-{obj.recommended_faces}-{obj.max_faces}"
    facing_display.short_description = 'フェース(最小-推奨-最大)'
    
    def price_display(self, obj):
        """価格表示"""
        if obj.price:
            return f"¥{obj.price:,.0f}"
        return "-"
    price_display.short_description = '価格'
    
    def placement_count(self, obj):
        """配置数"""
        count = obj.placements.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return 0
    placement_count.short_description = '配置数'
    
    def volume_display(self, obj):
        """体積表示"""
        return f"{obj.volume:.1f}cm³"
    volume_display.short_description = '体積'
    
    def recommended_width_display(self, obj):
        """推奨幅表示"""
        return f"{obj.recommended_width:.1f}cm"
    recommended_width_display.short_description = '推奨幅'
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:  # 編集時のみ計算値を表示
            fieldsets = fieldsets + (
                ('計算値', {
                    'fields': ('volume_display', 'recommended_width_display'),
                    'classes': ('collapse',),
                }),
            )
        return fieldsets