# apps/shelves/constraints.py
"""
配置制約チェック
"""
from django.core.exceptions import ValidationError


class PlacementConstraints:
    """配置制約チェッククラス"""
    
    @staticmethod
    def check_height_constraint(product, segment):
        """高さ制約チェック"""
        if product.height > segment.height:
            raise ValidationError(
                f'商品の高さ（{product.height}cm）が段の高さ（{segment.height}cm）を超えています'
            )
        return True
    
    @staticmethod
    def check_width_constraint(shelf, x_position, required_width):
        """幅制約チェック"""
        if x_position + required_width > shelf.width:
            raise ValidationError(
                f'配置位置が棚の幅（{shelf.width}cm）を超えています'
            )
        return True
    
    @staticmethod
    def check_overlap_constraint(segment, x_position, required_width, exclude_placement=None):
        """重複制約チェック"""
        from .models import ProductPlacement
        
        start_pos = x_position
        end_pos = x_position + required_width
        
        overlapping = ProductPlacement.objects.filter(
            segment=segment,
            is_active=True
        )
        
        if exclude_placement:
            overlapping = overlapping.exclude(id=exclude_placement.id)
        
        for placement in overlapping:
            existing_start = placement.x_position
            existing_end = placement.x_position + placement.occupied_width
            
            # 重複判定
            if not (end_pos <= existing_start or start_pos >= existing_end):
                raise ValidationError('他の商品と配置が重複しています')
        
        return True
    
    @staticmethod
    def check_face_count_constraint(product, face_count):
        """フェース数制約チェック"""
        if face_count < product.min_faces:
            raise ValidationError(
                f'フェース数は{product.min_faces}以上である必要があります'
            )
        
        if face_count > product.max_faces:
            raise ValidationError(
                f'フェース数は{product.max_faces}以下である必要があります'
            )
        
        return True
