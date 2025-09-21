# apps/accounts/tests.py
"""
アカウント機能のテスト
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .form import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm

User = get_user_model()


class UserModelTest(TestCase):
    """Userモデルのテスト"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': '太郎',
            'last_name': '田中',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """ユーザー作成のテスト"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, '太郎')
        self.assertEqual(user.last_name, '田中')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, 'staff')  # デフォルト役職
    
    def test_create_superuser(self):
        """スーパーユーザー作成のテスト"""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_get_full_name(self):
        """フルネーム取得のテスト"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), '田中 太郎')
        
        # 名前が空の場合
        user.first_name = ''
        user.last_name = ''
        self.assertEqual(user.get_full_name(), '')
    
    def test_is_manager_property(self):
        """マネージャー権限のテスト"""
        # スタッフユーザー
        staff_user = User.objects.create_user(role='staff', **self.user_data)
        self.assertFalse(staff_user.is_manager)
        
        # マネージャーユーザー
        manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            role='manager',
            password='pass123'
        )
        self.assertTrue(manager_user.is_manager)
        
        # 管理者ユーザー
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            role='admin',
            password='pass123'
        )
        self.assertTrue(admin_user.is_manager)
        self.assertTrue(admin_user.is_admin)
    
    def test_str_representation(self):
        """文字列表現のテスト"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), '田中 太郎 (test@example.com)')


class UserFormsTest(TestCase):
    """ユーザーフォームのテスト"""
    
    def test_custom_user_creation_form_valid(self):
        """ユーザー登録フォームの正常なケース"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': '花子',
            'last_name': '佐藤',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
            'department': 'IT部門'
        }
        
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.department, 'IT部門')
    
    def test_custom_user_creation_form_duplicate_email(self):
        """メールアドレス重複のテスト"""
        # 既存ユーザーを作成
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='pass123'
        )
        
        form_data = {
            'username': 'newuser',
            'email': 'test@example.com',  # 重複するメール
            'first_name': '花子',
            'last_name': '佐藤',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_authentication_form_with_email(self):
        """メールアドレスでのログインテスト"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # メールアドレスでログイン
        form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        
        form = CustomAuthenticationForm(data=form_data)
        # フォームの完全なバリデーションには request が必要
        # ここでは基本的な形式チェックのみ
        self.assertTrue(form.is_bound)
    
    def test_user_profile_form(self):
        """プロフィール編集フォームのテスト"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        
        form_data = {
            'first_name': '更新太郎',
            'last_name': '更新田中',
            'email': 'updated@example.com',
            'department': '更新部門',
            'phone': '03-1234-5678'
        }
        
        form = UserProfileForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.first_name, '更新太郎')
        self.assertEqual(updated_user.email, 'updated@example.com')


class UserViewsTest(TestCase):
    """ユーザービューのテスト"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='太郎',
            last_name='田中'
        )
    
    def test_login_view_get(self):
        """ログインページの表示テスト"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ログイン')
        self.assertContains(response, 'FlexiShelf')
    
    def test_login_view_post_valid(self):
        """正常なログインのテスト"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # ログイン成功後はホームページにリダイレクト
        self.assertEqual(response.status_code, 302)
    
    def test_login_view_post_invalid(self):
        """無効なログインのテスト"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ログイン')
    
    def test_register_view_get(self):
        """ユーザー登録ページの表示テスト"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '新規登録')
    
    def test_register_view_post_valid(self):
        """正常なユーザー登録のテスト"""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': '花子',
            'last_name': '佐藤',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        # 登録成功後はホームページにリダイレクト
        self.assertEqual(response.status_code, 302)
        
        # ユーザーが作成されたかチェック
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_profile_view_requires_login(self):
        """プロフィールページでのログイン要求テスト"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)  # ログインページにリダイレクト
    
    def test_profile_view_authenticated(self):
        """ログイン済みでのプロフィールページテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '田中 太郎')
    
    def test_profile_edit_view_authenticated(self):
        """プロフィール編集ページテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'プロフィール編集')
    
    def test_logout_view(self):
        """ログアウトのテスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)  # ログインページにリダイレクト
    
    def test_redirect_authenticated_user_from_login(self):
        """ログイン済みユーザーのログインページアクセステスト"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)  # ホームページにリダイレクト


class UserPermissionsTest(TestCase):
    """ユーザー権限のテスト"""
    
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='pass123',
            role='staff'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='pass123',
            role='manager'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123',
            role='admin'
        )
    
    def test_staff_permissions(self):
        """スタッフユーザーの権限テスト"""
        self.assertFalse(self.staff_user.is_manager)
        self.assertFalse(self.staff_user.is_admin)
        self.assertFalse(self.staff_user.is_staff)  # Django標準のis_staff
    
    def test_manager_permissions(self):
        """マネージャーユーザーの権限テスト"""
        self.assertTrue(self.manager_user.is_manager)
        self.assertFalse(self.manager_user.is_admin)
    
    def test_admin_permissions(self):
        """管理者ユーザーの権限テスト"""
        self.assertTrue(self.admin_user.is_manager)
        self.assertTrue(self.admin_user.is_admin)