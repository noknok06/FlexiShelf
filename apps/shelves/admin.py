"""
棚管理画面
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Shelf, ShelfSegment, ProductPlacement


class ShelfSegmentInline(admin.TabularInline):
    """棚段のインライン"""
    model = ShelfSegment
    extra = 1
    fields = ['level', 'height', 'y_position']
    readonly_fields = ['y_position']
    ordering = ['level']


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'dimensions_display', 'segment_count_display',
        'total_height_display', 'location', 'is_active'
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'location']
    ordering = ['name']
    list_editable = ['is_active']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'location', 'description')
        }),
        ('寸法', {
            'fields': ('width', 'depth'),
        }),
    )
    
    inlines = [ShelfSegmentInline]
    
    def dimensions_display(self, obj):
        """寸法表示"""
        return f"{obj.width}×{obj.depth}cm"
    dimensions_display.short_description = '寸法(W×D)'
    
    def segment_count_display(self, obj):
        """段数表示"""
        return f"{obj.segment_count}段"
    segment_count_display.short_description = '段数'
    
    def total_height_display(self, obj):
        """総高さ表示"""
        return f"{obj.total_height}cm"
    total_height_display.short_description = '総高さ'


class ProductPlacementInline(admin.TabularInline):
    """商品配置のインライン"""
    model = ProductPlacement
    extra = 0
    fields = ['product', 'x_position', 'face_count', 'occupied_width']
    readonly_fields = ['occupied_width']
    ordering = ['x_position']


@admin.register(ShelfSegment)
class ShelfSegmentAdmin(admin.ModelAdmin):
    list_display = [
        'shelf', 'level', 'height', 'y_position_display',
        'available_width_display', 'placement_count', 'is_active'
    ]
    list_filter = ['shelf', 'is_active']
    ordering = ['shelf', 'level']
    list_editable = ['height', 'is_active']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('shelf', 'level', 'height')
        }),
        ('計算値', {
            'fields': ('y_position',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['y_position']
    inlines = [ProductPlacementInline]
    
    def y_position_display(self, obj):
        """Y座標表示"""
        return f"{obj.y_position}cm"
    y_position_display.short_description = 'Y座標'
    
    def available_width_display(self, obj):
        """利用可能幅表示"""
        return f"{obj.available_width:.1f}cm"
    available_width_display.short_description = '利用可能幅'
    
    def placement_count(self, obj):
        """配置数"""
        return obj.placements.count()
    placement_count.short_description = '配置商品数'


@admin.register(ProductPlacement)
class ProductPlacementAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'shelf', 'segment_level', 'position_display',
        'face_count', 'occupied_width_display', 'is_active'
    ]
    list_filter = ['shelf', 'segment__level', 'product__manufacturer', 'is_active']
    search_fields = ['product__name', 'shelf__name']
    ordering = ['shelf', 'segment__level', 'x_position']
    list_editable = ['face_count', 'is_active']
    
    fieldsets = (
        ('配置先', {
            'fields': ('shelf', 'segment')
        }),
        ('商品・位置', {
            'fields': ('product', 'x_position', 'face_count')
        }),
        ('計算値', {
            'fields': ('occupied_width',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['occupied_width']
    
    def segment_level(self, obj):
        """段レベル"""
        return f"段{obj.segment.level}"
    segment_level.short_description = '段'
    
    def position_display(self, obj):
        """位置表示"""
        return f"{obj.x_position}-{obj.end_position}cm"
    position_display.short_description = '位置範囲'
    
    def occupied_width_display(self, obj):
        """占有幅表示"""
        return f"{obj.occupied_width}cm"
    occupied_width_display.short_description = '占有幅'