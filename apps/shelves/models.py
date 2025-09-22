"""
棚・陳列管理モデル
"""
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel
from apps.core.validators import validate_dimension, validate_positive_integer
from apps.products.models import Product


class Shelf(BaseModel):
    """棚マスタ"""
    name = models.CharField('棚名', max_length=100)
    width = models.FloatField(
        '幅(cm)',
        validators=[validate_dimension],
        help_text='棚の幅をcm単位で入力'
    )
    depth = models.FloatField(
        '奥行(cm)',
        validators=[validate_dimension],
        help_text='棚の奥行をcm単位で入力'
    )
    location = models.CharField('設置場所', max_length=200, blank=True)
    description = models.TextField('説明', blank=True)

    class Meta:
        verbose_name = '棚'
        verbose_name_plural = '棚'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.width}×{self.depth}cm)"

    @property
    def total_height(self):
        """棚の総高さ"""
        return sum(segment.height for segment in self.segments.all())

    @property
    def segment_count(self):
        """段数"""
        return self.segments.count()

    def get_available_width(self, segment_level):
        """指定段の利用可能幅を計算"""
        try:
            segment = self.segments.get(level=segment_level)
            used_width = sum(
                placement.occupied_width 
                for placement in segment.placements.all()
            )
            return self.width - used_width
        except ShelfSegment.DoesNotExist:
            return 0


class ShelfSegment(BaseModel):
    """棚の段（セグメント）"""
    shelf = models.ForeignKey(
        Shelf,
        on_delete=models.CASCADE,
        related_name='segments',
        verbose_name='棚'
    )
    level = models.IntegerField(
        '段番号',
        validators=[validate_positive_integer],
        help_text='1=最下段、2,3,4...上へ'
    )
    height = models.FloatField(
        '段高さ(cm)',
        validators=[validate_dimension],
        help_text='段の高さをcm単位で入力'
    )
    y_position = models.FloatField(
        '床からの位置(cm)',
        editable=False,
        help_text='自動計算される床からの高さ'
    )

    class Meta:
        verbose_name = '段'
        verbose_name_plural = '段'
        ordering = ['shelf', 'level']
        unique_together = ['shelf', 'level']

    def __str__(self):
        return f"{self.shelf.name} - 段{self.level}"

    def save(self, *args, **kwargs):
        """保存時にy_positionを自動計算"""
        if self.level == 1:
            self.y_position = 0
        else:
            # 下の段までの累積高さを計算
            lower_segments = ShelfSegment.objects.filter(
                shelf=self.shelf,
                level__lt=self.level,
                is_active=True
            ).order_by('level')
            self.y_position = sum(seg.height for seg in lower_segments)
        
        super().save(*args, **kwargs)
        
        # 上位の段のy_positionも更新
        self._update_upper_segments()

    def _update_upper_segments(self):
        """上位段のy_positionを更新"""
        upper_segments = ShelfSegment.objects.filter(
            shelf=self.shelf,
            level__gt=self.level,
            is_active=True
        ).order_by('level')
        
        for segment in upper_segments:
            lower_segments = ShelfSegment.objects.filter(
                shelf=self.shelf,
                level__lt=segment.level,
                is_active=True
            ).order_by('level')
            segment.y_position = sum(seg.height for seg in lower_segments)
            ShelfSegment.objects.filter(id=segment.id).update(y_position=segment.y_position)
                    
    @property
    def available_width(self):
        """利用可能幅"""
        used_width = sum(
            placement.occupied_width 
            for placement in self.placements.all()
        )
        return self.shelf.width - used_width

    def can_place_product(self, product, face_count=1):
        """商品が配置可能かチェック"""
        # 高さチェック
        if product.height > self.height:
            return False, f"商品の高さ（{product.height}cm）が段の高さ（{self.height}cm）を超えています"
        
        # 幅チェック
        required_width = product.width * face_count
        if required_width > self.available_width:
            return False, f"必要な幅（{required_width}cm）が利用可能幅（{self.available_width}cm）を超えています"
        
        return True, "配置可能"


class ProductPlacement(BaseModel):
    """商品配置"""
    shelf = models.ForeignKey(
        Shelf,
        on_delete=models.CASCADE,
        related_name='placements',
        verbose_name='棚'
    )
    segment = models.ForeignKey(
        ShelfSegment,
        on_delete=models.CASCADE,
        related_name='placements',
        verbose_name='段'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='placements',
        verbose_name='商品'
    )
    x_position = models.FloatField(
        'X座標(cm)',
        help_text='段内での左端からの距離'
    )
    face_count = models.IntegerField(
        'フェース数',
        default=1,
        validators=[validate_positive_integer],
        help_text='横並びの商品数'
    )
    occupied_width = models.FloatField(
        '占有幅(cm)',
        editable=False,
        help_text='自動計算される占有幅'
    )

    class Meta:
        verbose_name = '商品配置'
        verbose_name_plural = '商品配置'
        ordering = ['segment__level', 'x_position']
        indexes = [
            models.Index(fields=['shelf', 'segment']),
            models.Index(fields=['x_position']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.segment} ({self.face_count}面)"

    def save(self, *args, **kwargs):
        """保存時に占有幅を自動計算"""
        self.occupied_width = self.product.width * self.face_count
        super().save(*args, **kwargs)

    def clean(self):
        """モデルレベルのバリデーション"""
        errors = {}

        # 棚と段の整合性チェック
        if self.segment.shelf != self.shelf:
            errors['segment'] = '指定された段は指定された棚に属していません。'

        # フェース数制約チェック
        if self.face_count < self.product.min_faces:
            errors['face_count'] = f'フェース数は{self.product.min_faces}以上である必要があります。'
        
        if self.face_count > self.product.max_faces:
            errors['face_count'] = f'フェース数は{self.product.max_faces}以下である必要があります。'

        # 物理制約チェック
        if self.product.height > self.segment.height:
            errors['product'] = f'商品の高さ（{self.product.height}cm）が段の高さ（{self.segment.height}cm）を超えています。'

        # 幅制約チェック
        required_width = self.product.width * self.face_count
        if self.x_position + required_width > self.shelf.width:
            errors['x_position'] = f'配置位置が棚の幅（{self.shelf.width}cm）を超えています。'

        # 重複チェック
        if self._check_overlap():
            errors['x_position'] = '他の商品と配置が重複しています。'

        if errors:
            raise ValidationError(errors)

    def _check_overlap(self):
        """他の配置との重複をチェック"""
        new_start = self.x_position
        new_end = self.x_position + (self.product.width * self.face_count)
        
        # 同じ段の他の配置をチェック
        other_placements = ProductPlacement.objects.filter(
            segment=self.segment,
            is_active=True
        )
        
        # 自分自身を除外
        if self.pk:
            other_placements = other_placements.exclude(pk=self.pk)
        
        for placement in other_placements:
            existing_start = placement.x_position
            existing_end = placement.x_position + placement.occupied_width
            
            # 重複判定
            if not (new_end <= existing_start or new_start >= existing_end):
                return True
        
        return False

    @property
    def end_position(self):
        """終了位置（X座標 + 占有幅）"""
        return self.x_position + self.occupied_width