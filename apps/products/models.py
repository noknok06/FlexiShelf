"""
商品管理モデル
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.core.validators import validate_dimension, validate_face_count


class Category(BaseModel):
    """商品カテゴリ"""
    name = models.CharField('カテゴリ名', max_length=100, unique=True)
    code = models.CharField('カテゴリコード', max_length=20, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='親カテゴリ'
    )
    sort_order = models.IntegerField('表示順', default=0)

    class Meta:
        verbose_name = 'カテゴリ'
        verbose_name_plural = 'カテゴリ'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Manufacturer(BaseModel):
    """メーカー"""
    name = models.CharField('メーカー名', max_length=100, unique=True)
    code = models.CharField('メーカーコード', max_length=20, unique=True)
    is_own_company = models.BooleanField('自社', default=False)

    class Meta:
        verbose_name = 'メーカー'
        verbose_name_plural = 'メーカー'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(BaseModel):
    """商品"""
    
    SIZE_CHOICES = [
        ('small', '小型'),
        ('medium', '中型'),
        ('large', '大型'),
    ]
    
    name = models.CharField('商品名', max_length=200)
    jan_code = models.CharField('JANコード', max_length=13, unique=True, null=True, blank=True)
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='メーカー'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='カテゴリ'
    )
    
    # 物理寸法（cm）
    width = models.FloatField(
        '幅(cm)',
        validators=[validate_dimension],
        help_text='商品の幅（横）をcm単位で入力'
    )
    height = models.FloatField(
        '高さ(cm)',
        validators=[validate_dimension],
        help_text='商品の高さをcm単位で入力'
    )
    depth = models.FloatField(
        '奥行(cm)',
        validators=[validate_dimension],
        help_text='商品の奥行をcm単位で入力'
    )
    
    # フェーシング制約
    min_faces = models.IntegerField(
        '最小フェース数',
        default=1,
        validators=[validate_face_count]
    )
    max_faces = models.IntegerField(
        '最大フェース数',
        default=10,
        validators=[validate_face_count]
    )
    recommended_faces = models.IntegerField(
        '推奨フェース数',
        default=1,
        validators=[validate_face_count]
    )
    
    # その他属性
    size_category = models.CharField(
        'サイズ区分',
        max_length=10,
        choices=SIZE_CHOICES,
        blank=True
    )
    price = models.DecimalField(
        '価格',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    image = models.ImageField(
        '商品画像',
        upload_to='products/images/',
        null=True,
        blank=True
    )
    description = models.TextField('商品説明', blank=True)

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['manufacturer', 'name']
        indexes = [
            models.Index(fields=['jan_code']),
            models.Index(fields=['manufacturer', 'category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.manufacturer.name})"

    @property
    def is_own_product(self):
        """自社商品かどうか"""
        return self.manufacturer.is_own_company

    @property
    def volume(self):
        """体積（cm³）"""
        return self.width * self.height * self.depth

    def clean(self):
        """モデルレベルのバリデーション"""
        from django.core.exceptions import ValidationError
        
        # フェース数の整合性チェック
        if self.min_faces > self.max_faces:
            raise ValidationError({
                'min_faces': '最小フェース数は最大フェース数以下である必要があります。'
            })
        
        if not (self.min_faces <= self.recommended_faces <= self.max_faces):
            raise ValidationError({
                'recommended_faces': '推奨フェース数は最小・最大フェース数の範囲内である必要があります。'
            })

    def get_optimal_facing(self, available_width):
        """利用可能幅に対する最適フェース数を計算"""
        max_possible = int(available_width // self.width)
        return min(max_possible, self.max_faces, self.recommended_faces + 2)