from django.db import transaction
from django.db.models import Avg
from django.core.exceptions import ValidationError
from .models import Product, Category, Manufacturer


class ProductService:
    """商品管理サービス"""
    
    @staticmethod
    def create_product_with_validation(product_data, user):
        """バリデーション付き商品作成"""
        with transaction.atomic():
            # 基本バリデーション
            if not product_data.get('name'):
                raise ValidationError('商品名は必須です')
            
            # 重複チェック（JANコード）
            jan_code = product_data.get('jan_code')
            if jan_code and Product.objects.filter(
                jan_code=jan_code, 
                is_active=True
            ).exists():
                raise ValidationError('このJANコードは既に使用されています')
            
            # 商品作成
            product = Product.objects.create(
                **product_data,
                created_by=user
            )
            
            return product
    
    @staticmethod
    def bulk_import_products(csv_data, user):
        """CSV一括インポート"""
        # 将来の実装用
        raise NotImplementedError('CSV一括インポート機能は今後実装予定です')
    
    @staticmethod
    def get_product_placement_stats(product):
        """商品の配置統計を取得"""
        placements = product.placements.filter(is_active=True)
        
        if not placements.exists():
            return None
            
        return {
            'placement_count': placements.count(),
            'total_faces': sum(p.face_count for p in placements),
            'shelf_count': placements.values('shelf').distinct().count(),
            'avg_faces': placements.aggregate(avg=Avg('face_count'))['avg'] or 0,
        }


