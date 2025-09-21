"""
商品管理画面
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Manufacturer, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'sort_order', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'code']
    ordering = ['sort_order', 'name']
    list_editable = ['sort_order', 'is_active']


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_own_company', 'is_active']
    list_filter = ['is_own_company', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['name']
    list_editable = ['is_own_company', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'manufacturer', 'category', 'dimensions_display',
        'facing_info', 'is_own_product', 'is_active'
    ]
    list_filter = [
        'manufacturer__is_own_company', 'category', 'size_category',
        'manufacturer', 'is_active'
    ]
    search_fields = ['name', 'jan_code', 'manufacturer__name']
    ordering = ['manufacturer', 'name']
    list_editable = ['is_active']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'jan_code', 'manufacturer', 'category', 'description')
        }),
        ('物理寸法', {
            'fields': ('width', 'height', 'depth', 'size_category'),
            'classes': ('collapse',)
        }),
        ('フェーシング設定', {
            'fields': ('min_faces', 'max_faces', 'recommended_faces'),
            'classes': ('collapse',)
        }),
        ('その他', {
            'fields': ('price', 'image'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['volume_display']
    
    def dimensions_display(self, obj):
        """寸法表示"""
        return f"{obj.width}×{obj.height}×{obj.depth}cm"
    dimensions_display.short_description = '寸法(W×H×D)'
    
    def facing_info(self, obj):
        """フェーシング情報"""
        return f"{obj.min_faces}-{obj.max_faces}面 (推奨: {obj.recommended_faces})"
    facing_info.short_description = 'フェーシング'
    
    def is_own_product(self, obj):
        """自社商品判定"""
        if obj.manufacturer.is_own_company:
            return format_html('<span style="color: green;">●</span> 自社')
        return format_html('<span style="color: orange;">●</span> 競合')
    is_own_product.short_description = '区分'
    
    def volume_display(self, obj):
        """体積表示"""
        return f"{obj.volume:.2f}cm³"
    volume_display.short_description = '体積'