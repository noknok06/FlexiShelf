"""
商品管理フォーム
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category, Manufacturer


class ProductForm(forms.ModelForm):
    """商品作成・編集フォーム"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'jan_code', 'manufacturer', 'category',
            'width', 'height', 'depth', 'size_category',
            'min_faces', 'max_faces', 'recommended_faces',
            'price', 'image', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '商品名を入力'
            }),
            'jan_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '13桁のJANコード',
                'maxlength': '13'
            }),
            'manufacturer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'cm'
            }),
            'height': forms.NumberInput(attrs={
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
            'size_category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'min_faces': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'max_faces': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'recommended_faces': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': '商品の説明を入力'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # フィールドラベルの設定
        self.fields['name'].label = '商品名'
        self.fields['jan_code'].label = 'JANコード'
        self.fields['manufacturer'].label = 'メーカー'
        self.fields['category'].label = 'カテゴリ'
        self.fields['width'].label = '幅 (cm)'
        self.fields['height'].label = '高さ (cm)'
        self.fields['depth'].label = '奥行 (cm)'
        self.fields['size_category'].label = 'サイズ区分'
        self.fields['min_faces'].label = '最小フェース数'
        self.fields['max_faces'].label = '最大フェース数'
        self.fields['recommended_faces'].label = '推奨フェース数'
        self.fields['price'].label = '価格'
        self.fields['image'].label = '商品画像'
        self.fields['description'].label = '説明'
        
        # 必須フィールドのマーク
        required_fields = ['name', 'manufacturer', 'category', 'width', 'height', 'depth']
        for field_name in required_fields:
            self.fields[field_name].required = True
        
        # ヘルプテキストの設定
        self.fields['jan_code'].help_text = '13桁のJANコードを入力（オプション）'
        self.fields['width'].help_text = '商品の幅をcm単位で入力'
        self.fields['height'].help_text = '商品の高さをcm単位で入力'
        self.fields['depth'].help_text = '商品の奥行をcm単位で入力'
        self.fields['min_faces'].help_text = '最低限必要なフェース数'
        self.fields['max_faces'].help_text = '最大配置可能なフェース数'
        self.fields['recommended_faces'].help_text = '推奨フェース数'

    def clean_jan_code(self):
        """JANコードのバリデーション"""
        jan_code = self.cleaned_data.get('jan_code')
        if jan_code:
            # 数字のみかチェック
            if not jan_code.isdigit():
                raise ValidationError('JANコードは数字のみで入力してください。')
            
            # 13桁かチェック
            if len(jan_code) != 13:
                raise ValidationError('JANコードは13桁で入力してください。')
            
            # 重複チェック
            existing_product = Product.objects.filter(
                jan_code=jan_code,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_product.exists():
                raise ValidationError('このJANコードは既に使用されています。')
        
        return jan_code

    def clean(self):
        """フォーム全体のバリデーション"""
        cleaned_data = super().clean()
        min_faces = cleaned_data.get('min_faces')
        max_faces = cleaned_data.get('max_faces')
        recommended_faces = cleaned_data.get('recommended_faces')

        # フェース数の整合性チェック
        if min_faces and max_faces:
            if min_faces > max_faces:
                raise ValidationError({
                    'min_faces': '最小フェース数は最大フェース数以下である必要があります。'
                })

        if min_faces and recommended_faces and max_faces:
            if not (min_faces <= recommended_faces <= max_faces):
                raise ValidationError({
                    'recommended_faces': '推奨フェース数は最小・最大フェース数の範囲内である必要があります。'
                })

        return cleaned_data


class ProductSearchForm(forms.Form):
    """商品検索フォーム"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '商品名、JANコード、メーカー名で検索',
            'autocomplete': 'off'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label='全カテゴリ',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    manufacturer = forms.ModelChoiceField(
        queryset=Manufacturer.objects.filter(is_active=True),
        required=False,
        empty_label='全メーカー',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_own = forms.ChoiceField(
        choices=[
            ('', '全商品'),
            ('true', '自社商品'),
            ('false', '競合商品'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    size_category = forms.ChoiceField(
        choices=[('', '全サイズ')] + Product.SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # フィールドラベルの設定
        self.fields['search'].label = 'キーワード検索'
        self.fields['category'].label = 'カテゴリ'
        self.fields['manufacturer'].label = 'メーカー'
        self.fields['is_own'].label = '商品区分'
        self.fields['size_category'].label = 'サイズ区分'


class CategoryForm(forms.ModelForm):
    """カテゴリ作成・編集フォーム"""
    
    class Meta:
        model = Category
        fields = ['name', 'code', 'parent', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'カテゴリ名を入力'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'カテゴリコードを入力'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }


class ManufacturerForm(forms.ModelForm):
    """メーカー作成・編集フォーム"""
    
    class Meta:
        model = Manufacturer
        fields = ['name', 'code', 'is_own_company']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'メーカー名を入力'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'メーカーコードを入力'
            }),
            'is_own_company': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }