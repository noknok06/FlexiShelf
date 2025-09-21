# apps/accounts/forms.py
"""
ユーザー認証フォーム
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """カスタムユーザー登録フォーム"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'メールアドレスを入力'
        })
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '名を入力'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '姓を入力'
        })
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '部署名を入力（任意）'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'department')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ユーザー名を入力'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # フィールドラベルの設定
        self.fields['username'].label = 'ユーザー名'
        self.fields['email'].label = 'メールアドレス'
        self.fields['first_name'].label = '名'
        self.fields['last_name'].label = '姓'
        self.fields['password1'].label = 'パスワード'
        self.fields['password2'].label = 'パスワード（確認）'
        self.fields['department'].label = '部署'
        
        # パスワードフィールドのクラス設定
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'パスワードを入力'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'パスワードを再入力'
        })
        
        # ヘルプテキストの設定
        self.fields['username'].help_text = '150文字以下。英数字と @/./+/-/_ のみ使用可能'
        self.fields['email'].help_text = 'ログイン時に使用します'
        self.fields['password1'].help_text = '8文字以上で、一般的でないパスワードを設定してください'

    def clean_email(self):
        """メールアドレスの重複チェック"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('このメールアドレスは既に使用されています。')
        return email

    def save(self, commit=True):
        """ユーザー保存"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.department = self.cleaned_data.get('department', '')
        
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """カスタムログインフォーム"""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'ユーザー名またはメールアドレス',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'パスワード'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'ユーザー名またはメールアドレス'
        self.fields['password'].label = 'パスワード'

    def clean(self):
        """メールアドレスでのログイン対応"""
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            # メールアドレスでログインを試行
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    username = user.username
                except User.DoesNotExist:
                    pass
            
            self.user_cache = authenticate(
                self.request, 
                username=username, 
                password=password
            )
            
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    """ユーザープロフィール編集フォーム"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'department', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # フィールドラベルの設定
        self.fields['first_name'].label = '名'
        self.fields['last_name'].label = '姓'
        self.fields['email'].label = 'メールアドレス'
        self.fields['department'].label = '部署'
        self.fields['phone'].label = '電話番号'
        
        # 必須フィールドの設定
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        """メールアドレスの重複チェック（自分以外）"""
        email = self.cleaned_data.get('email')
        if self.instance and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('このメールアドレスは既に使用されています。')
        return email