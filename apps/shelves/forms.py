"""
棚管理フォーム
"""
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Shelf, ShelfSegment, ProductPlacement
from apps.products.models import Product


class ShelfForm(forms.ModelForm):
    """棚作成・編集フォーム"""
    
    class Meta:
        model = Shelf
        fields = ['name', 'width', 'depth', 'location', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '棚名を入力'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'cm'
            }),
            'depth': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'cm'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '設置場所を入力'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '棚の説明を入力'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # フィールドラベルの設定
        self.fields['name'].label = '棚名'
        self.fields['width'].label = '幅 (cm)'
        self.fields['depth'].label = '奥行 (cm)'
        self.fields['location'].label = '設置場所'
        self.fields['description'].label = '説明'
        
        # 必須フィールドのマーク
        required_fields = ['name', 'width', 'depth']
        for field_name in required_fields:
            self.fields[field_name].required = True
        
        # ヘルプテキストの設定
        self.fields['width'].help_text = '棚の幅をcm単位で入力'
        self.fields['depth'].help_text = '棚の奥行をcm単位で入力'
        self.fields['location'].help_text = '例: エンド什器A、レジ横棚'


class ShelfSegmentForm(forms.ModelForm):
    """棚段フォーム"""
    
    class Meta:
        model = ShelfSegment
        fields = ['level', 'height']
        widgets = {
            'level': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '1',
                'readonly': True,  # JavaScript で自動設定
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'cm'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['level'].label = '段番号'
        self.fields['height'].label = '高さ (cm)'


# 棚段のフォームセット
ShelfSegmentFormSet = inlineformset_factory(
    Shelf, 
    ShelfSegment,
    form=ShelfSegmentForm,
    extra=4,  # デフォルトで4段
    max_num=10,  # 最大10段
    can_delete=True,
    can_delete_extra=True,
)


class ProductPlacementForm(forms.ModelForm):
    """商品配置フォーム"""
    
    product_search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '商品名で検索...',
            'autocomplete': 'off',
            'data-toggle': 'product-search'
        })
    )
    
    class Meta:
        model = ProductPlacement
        fields = ['segment', 'product', 'x_position', 'face_count']
        widgets = {
            'segment': forms.Select(attrs={
                'class': 'form-select'
            }),
            'product': forms.Select(attrs={
                'class': 'form-select'
            }),
            'x_position': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'cm'
            }),
            'face_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '面数'
            }),
        }

    def __init__(self, *args, **kwargs):
        shelf = kwargs.pop('shelf', None)
        super().__init__(*args, **kwargs)
        
        # フィールドラベルの設定
        self.fields['segment'].label = '配置段'
        self.fields['product'].label = '商品'
        self.fields['x_position'].label = 'X座標 (cm)'
        self.fields['face_count'].label = 'フェース数'
        self.fields['product_search'].label = '商品検索'
        
        # 棚が指定されている場合、その棚の段のみ表示
        if shelf:
            self.fields['segment'].queryset = ShelfSegment.objects.filter(
                shelf=shelf, 
                is_active=True
            ).order_by('level')
        
        # 商品リストをアクティブなもののみに限定
        self.fields['product'].queryset = Product.objects.filter(
            is_active=True
        ).select_related('manufacturer').order_by('manufacturer__name', 'name')
        
        # ヘルプテキスト
        self.fields['x_position'].help_text = '段の左端からの距離'
        self.fields['face_count'].help_text = '横並びに配置する商品数'

    def clean(self):
        """フォーム全体のバリデーション"""
        cleaned_data = super().clean()
        segment = cleaned_data.get('segment')
        product = cleaned_data.get('product')
        x_position = cleaned_data.get('x_position')
        face_count = cleaned_data.get('face_count')

        if segment and product and x_position is not None and face_count:
            # 配置可能性チェック
            can_place, message = segment.can_place_product(product, face_count)
            if not can_place:
                raise ValidationError(message)
            
            # 位置チェック
            required_width = product.width * face_count
            if x_position + required_width > segment.shelf.width:
                raise ValidationError({
                    'x_position': f'指定位置では棚幅を超過します（必要幅: {required_width}cm）'
                })

        return cleaned_data


class ShelfSearchForm(forms.Form):
    """棚検索フォーム"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '棚名、設置場所で検索',
            'autocomplete': 'off'
        })
    )
    
    has_placements = forms.ChoiceField(
        choices=[
            ('', '全て'),
            ('true', '商品配置あり'),
            ('false', '商品配置なし'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    min_width = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0',
            'placeholder': '最小幅(cm)'
        })
    )
    
    max_width = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0',
            'placeholder': '最大幅(cm)'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # フィールドラベルの設定
        self.fields['search'].label = 'キーワード検索'
        self.fields['has_placements'].label = '配置状況'
        self.fields['min_width'].label = '最小幅'
        self.fields['max_width'].label = '最大幅'

    def clean(self):
        """フォーム全体のバリデーション"""
        cleaned_data = super().clean()
        min_width = cleaned_data.get('min_width')
        max_width = cleaned_data.get('max_width')

        if min_width and max_width and min_width > max_width:
            raise ValidationError('最小幅は最大幅以下である必要があります。')

        return cleaned_data


class BulkPlacementForm(forms.Form):
    """一括配置フォーム"""
    
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        label='配置する商品'
    )
    
    target_segment = forms.ModelChoiceField(
        queryset=ShelfSegment.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='配置先の段'
    )
    
    default_face_count = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        }),
        label='デフォルトフェース数'
    )
    
    auto_arrange = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='自動配置',
        help_text='幅に合わせて自動的に配置位置を決定'
    )

    def __init__(self, *args, **kwargs):
        shelf = kwargs.pop('shelf', None)
        super().__init__(*args, **kwargs)
        
        if shelf:
            self.fields['target_segment'].queryset = ShelfSegment.objects.filter(
                shelf=shelf,
                is_active=True
            ).order_by('level')

    def clean(self):
        """一括配置のバリデーション"""
        cleaned_data = super().clean()
        products = cleaned_data.get('products')
        target_segment = cleaned_data.get('target_segment')
        face_count = cleaned_data.get('default_face_count', 1)

        if products and target_segment:
            # 全商品が配置可能かチェック
            total_width = 0
            for product in products:
                total_width += product.width * face_count
            
            if total_width > target_segment.available_width:
                raise ValidationError(
                    f'選択した商品の合計幅（{total_width:.1f}cm）が'
                    f'利用可能幅（{target_segment.available_width:.1f}cm）を超えています。'
                )

        return cleaned_data