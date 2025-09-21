# utils/exporters.py
"""
データエクスポート機能
"""
import csv
import json
from django.http import HttpResponse
from django.template.loader import render_to_string


def export_products_csv(products):
    """商品データのCSVエクスポート"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    response.write('\ufeff')  # BOM for Excel
    
    writer = csv.writer(response)
    writer.writerow([
        '商品名', 'JANコード', 'メーカー', 'カテゴリ', 
        '幅(cm)', '高さ(cm)', '奥行(cm)', 
        '最小フェース', '最大フェース', '推奨フェース',
        '価格', '自社商品'
    ])
    
    for product in products:
        writer.writerow([
            product.name,
            product.jan_code or '',
            product.manufacturer.name,
            product.category.name,
            product.width,
            product.height,
            product.depth,
            product.min_faces,
            product.max_faces,
            product.recommended_faces,
            product.price or '',
            '○' if product.is_own_product else '×'
        ])
    
    return response


def export_shelf_layout_json(shelf):
    """棚レイアウトのJSONエクスポート"""
    data = {
        'shelf': {
            'id': shelf.id,
            'name': shelf.name,
            'width': shelf.width,
            'depth': shelf.depth,
            'location': shelf.location,
        },
        'segments': [],
        'placements': []
    }
    
    for segment in shelf.segments.filter(is_active=True).order_by('level'):
        data['segments'].append({
            'id': segment.id,
            'level': segment.level,
            'height': segment.height,
            'y_position': segment.y_position,
        })
        
        for placement in segment.placements.filter(is_active=True).order_by('x_position'):
            data['placements'].append({
                'id': placement.id,
                'segment_level': segment.level,
                'product_name': placement.product.name,
                'product_jan': placement.product.jan_code,
                'manufacturer': placement.product.manufacturer.name,
                'x_position': placement.x_position,
                'face_count': placement.face_count,
                'occupied_width': placement.occupied_width,
            })
    
    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="shelf_{shelf.id}_layout.json"'
    return response