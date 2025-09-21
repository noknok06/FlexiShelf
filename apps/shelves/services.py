# apps/shelves/services.py
"""
棚管理ビジネスロジック
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Shelf, ShelfSegment, ProductPlacement


class ShelfService:
    """棚管理サービス"""
    
    @staticmethod
    def create_shelf_with_segments(shelf_data, segments_data, user):
        """段付き棚作成"""
        with transaction.atomic():
            # 棚作成
            shelf = Shelf.objects.create(
                **shelf_data,
                created_by=user
            )
            
            # 段作成
            for level, segment_data in enumerate(segments_data, 1):
                ShelfSegment.objects.create(
                    shelf=shelf,
                    level=level,
                    height=segment_data['height'],
                    created_by=user
                )
            
            return shelf
    
    @staticmethod
    def validate_placement(shelf, segment, product, x_position, face_count):
        """配置バリデーション"""
        errors = []
        
        # 高さチェック
        if product.height > segment.height:
            errors.append(f'商品の高さ（{product.height}cm）が段の高さ（{segment.height}cm）を超えています')
        
        # 幅チェック
        required_width = product.width * face_count
        if x_position + required_width > shelf.width:
            errors.append(f'配置位置が棚の幅を超えます（必要幅: {required_width}cm）')
        
        # 重複チェック
        overlapping = ProductPlacement.objects.filter(
            segment=segment,
            is_active=True
        ).exclude(
            x_position__gte=x_position + required_width
        ).exclude(
            x_position__lte=x_position - product.width
        )
        
        if overlapping.exists():
            errors.append('他の商品と配置が重複します')
        
        return errors
    
    @staticmethod
    def optimize_shelf_layout(shelf):
        """棚レイアウト最適化"""
        # 将来の実装用
        raise NotImplementedError('レイアウト最適化機能は今後実装予定です')
