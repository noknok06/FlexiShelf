# apps/core/management/commands/setup_demo_data.py
"""
デモデータ作成コマンド
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.products.models import Category, Manufacturer, Product
from apps.shelves.models import Shelf, ShelfSegment, ProductPlacement

User = get_user_model()


class Command(BaseCommand):
    help = 'デモデータを作成します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='既存のデモデータを削除してから作成'
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('既存のデモデータを削除中...')
            self.reset_demo_data()

        self.stdout.write('デモデータを作成中...')
        
        with transaction.atomic():
            # 管理者ユーザー作成
            admin_user = self.create_admin_user()
            
            # カテゴリ作成
            categories = self.create_categories()
            
            # メーカー作成
            manufacturers = self.create_manufacturers()
            
            # 商品作成
            products = self.create_products(categories, manufacturers, admin_user)
            
            # 棚作成
            shelves = self.create_shelves(admin_user)
            
            # 段作成
            self.create_segments(shelves, admin_user)
            
            # サンプル配置作成
            self.create_sample_placements(shelves, products, admin_user)

        self.stdout.write(
            self.style.SUCCESS('デモデータの作成が完了しました！')
        )
        self.stdout.write('管理者ユーザー: admin / パスワード: admin123')

    def reset_demo_data(self):
        """既存のデモデータを削除"""
        ProductPlacement.objects.all().delete()
        ShelfSegment.objects.all().delete()
        Shelf.objects.all().delete()
        Product.objects.all().delete()
        Manufacturer.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(username='admin').delete()

    def create_admin_user(self):
            """管理者ユーザー作成"""
            admin_user, created = User.objects.get_or_create(
                email='admin@flexishelf.com',  # メールアドレスをキーにする
                defaults={
                    'username': 'admin',
                    'first_name': '管理者',
                    'last_name': 'システム',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_email_verified': True,
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write(f'管理者ユーザー "{admin_user.email}" を作成しました')
            
            # スタッフユーザーも作成
            staff_user, created = User.objects.get_or_create(
                email='staff@flexishelf.com',
                defaults={
                    'username': 'staff',
                    'first_name': 'スタッフ',
                    'last_name': 'テスト',
                    'role': 'staff',
                    'is_staff': False,
                    'is_superuser': False,
                    'is_email_verified': True,
                }
            )
            if created:
                staff_user.set_password('staff123')
                staff_user.save()
                self.stdout.write(f'スタッフユーザー "{staff_user.email}" を作成しました')
            
            return admin_user
        
    def create_categories(self):
        """カテゴリ作成"""
        categories_data = [
            {'name': '飲料', 'code': 'DRINK'},
            {'name': '菓子', 'code': 'SNACK'},
            {'name': '日用品', 'code': 'DAILY'},
            {'name': '食品', 'code': 'FOOD'},
            {'name': '冷凍食品', 'code': 'FROZEN'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                code=cat_data['code'],
                defaults=cat_data
            )
            categories[cat_data['code']] = category
            if created:
                self.stdout.write(f'カテゴリ "{category.name}" を作成しました')
        
        return categories

    def create_manufacturers(self):
        """メーカー作成"""
        manufacturers_data = [
            {'name': 'コカ・コーラ', 'code': 'COCA', 'is_own_company': False},
            {'name': 'サントリー', 'code': 'SUNTORY', 'is_own_company': False},
            {'name': 'キリン', 'code': 'KIRIN', 'is_own_company': False},
            {'name': '自社ブランド', 'code': 'OWN', 'is_own_company': True},
            {'name': 'カルビー', 'code': 'CALBEE', 'is_own_company': False},
            {'name': 'ロッテ', 'code': 'LOTTE', 'is_own_company': False},
            {'name': 'P&G', 'code': 'PG', 'is_own_company': False},
            {'name': '花王', 'code': 'KAO', 'is_own_company': False},
        ]
        
        manufacturers = {}
        for manu_data in manufacturers_data:
            manufacturer, created = Manufacturer.objects.get_or_create(
                code=manu_data['code'],
                defaults=manu_data
            )
            manufacturers[manu_data['code']] = manufacturer
            if created:
                self.stdout.write(f'メーカー "{manufacturer.name}" を作成しました')
        
        return manufacturers

    def create_products(self, categories, manufacturers, user):
        """商品作成"""
        products_data = [
            # 飲料
            {'name': 'コカ・コーラ 500ml', 'manufacturer': 'COCA', 'category': 'DRINK', 
             'width': 6.5, 'height': 20.5, 'depth': 6.5, 'min_faces': 1, 'max_faces': 6, 'recommended_faces': 3},
            {'name': 'ペプシコーラ 500ml', 'manufacturer': 'SUNTORY', 'category': 'DRINK',
             'width': 6.5, 'height': 20.5, 'depth': 6.5, 'min_faces': 1, 'max_faces': 6, 'recommended_faces': 2},
            {'name': 'キリン 午後の紅茶 500ml', 'manufacturer': 'KIRIN', 'category': 'DRINK',
             'width': 6.5, 'height': 20.5, 'depth': 6.5, 'min_faces': 1, 'max_faces': 4, 'recommended_faces': 2},
            {'name': '自社ブランド 緑茶 500ml', 'manufacturer': 'OWN', 'category': 'DRINK',
             'width': 6.5, 'height': 20.5, 'depth': 6.5, 'min_faces': 2, 'max_faces': 8, 'recommended_faces': 4},
            
            # 菓子
            {'name': 'ポテトチップス うすしお', 'manufacturer': 'CALBEE', 'category': 'SNACK',
             'width': 15.0, 'height': 25.0, 'depth': 8.0, 'min_faces': 1, 'max_faces': 3, 'recommended_faces': 2},
            {'name': 'チョコパイ', 'manufacturer': 'LOTTE', 'category': 'SNACK',
             'width': 12.0, 'height': 18.0, 'depth': 6.0, 'min_faces': 1, 'max_faces': 4, 'recommended_faces': 2},
            {'name': '自社ブランド クッキー', 'manufacturer': 'OWN', 'category': 'SNACK',
             'width': 10.0, 'height': 15.0, 'depth': 5.0, 'min_faces': 2, 'max_faces': 6, 'recommended_faces': 3},
            
            # 日用品
            {'name': 'アリエール 洗濯洗剤', 'manufacturer': 'PG', 'category': 'DAILY',
             'width': 18.0, 'height': 25.0, 'depth': 12.0, 'min_faces': 1, 'max_faces': 2, 'recommended_faces': 1},
            {'name': 'アタック 洗濯洗剤', 'manufacturer': 'KAO', 'category': 'DAILY',
             'width': 18.0, 'height': 25.0, 'depth': 12.0, 'min_faces': 1, 'max_faces': 2, 'recommended_faces': 1},
            {'name': '自社ブランド 柔軟剤', 'manufacturer': 'OWN', 'category': 'DAILY',
             'width': 15.0, 'height': 22.0, 'depth': 10.0, 'min_faces': 1, 'max_faces': 3, 'recommended_faces': 2},
        ]
        
        products = []
        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'manufacturer': manufacturers[prod_data['manufacturer']],
                    'category': categories[prod_data['category']],
                    'width': prod_data['width'],
                    'height': prod_data['height'],
                    'depth': prod_data['depth'],
                    'min_faces': prod_data['min_faces'],
                    'max_faces': prod_data['max_faces'],
                    'recommended_faces': prod_data['recommended_faces'],
                    'created_by': user,
                }
            )
            products.append(product)
            if created:
                self.stdout.write(f'商品 "{product.name}" を作成しました')
        
        return products

    def create_shelves(self, user):
        """棚作成"""
        shelves_data = [
            {'name': 'エンド陳列棚A', 'width': 120.0, 'depth': 40.0, 'location': 'レジ横エンド'},
            {'name': 'ゴンドラ棚B-1', 'width': 180.0, 'depth': 45.0, 'location': '飲料コーナー'},
            {'name': '冷蔵ケース棚C', 'width': 150.0, 'depth': 60.0, 'location': '冷蔵コーナー'},
        ]
        
        shelves = []
        for shelf_data in shelves_data:
            shelf, created = Shelf.objects.get_or_create(
                name=shelf_data['name'],
                defaults={
                    **shelf_data,
                    'created_by': user,
                }
            )
            shelves.append(shelf)
            if created:
                self.stdout.write(f'棚 "{shelf.name}" を作成しました')
        
        return shelves

    def create_segments(self, shelves, user):
        """段作成"""
        for shelf in shelves:
            # 各棚に4段ずつ作成
            for level in range(1, 5):
                segment, created = ShelfSegment.objects.get_or_create(
                    shelf=shelf,
                    level=level,
                    defaults={
                        'height': 30.0 + (level * 2),  # 段により高さを調整
                        'created_by': user,
                    }
                )
                if created:
                    self.stdout.write(f'段 "{shelf.name} - 段{level}" を作成しました')

    def create_sample_placements(self, shelves, products, user):
        """サンプル配置作成"""
        import random
        
        for shelf in shelves:
            segments = list(shelf.segments.all())
            
            # 各段にランダムに商品を配置
            for segment in segments:
                available_width = shelf.width
                x_position = 0
                
                # 段にランダムに2-4商品を配置
                num_products = random.randint(2, 4)
                selected_products = random.sample(products, min(num_products, len(products)))
                
                for product in selected_products:
                    if available_width < product.width:
                        break
                    
                    # 配置可能かチェック
                    if product.height <= segment.height:
                        face_count = random.randint(
                            product.min_faces, 
                            min(product.max_faces, int(available_width // product.width))
                        )
                        
                        try:
                            placement = ProductPlacement.objects.create(
                                shelf=shelf,
                                segment=segment,
                                product=product,
                                x_position=x_position,
                                face_count=face_count,
                                created_by=user,
                            )
                            
                            x_position += placement.occupied_width + 2  # 2cmの間隔
                            available_width -= placement.occupied_width + 2
                            
                            self.stdout.write(
                                f'配置 "{product.name}" を "{shelf.name} - 段{segment.level}" に作成しました'
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'配置作成に失敗: {product.name} - {e}')
                            )
