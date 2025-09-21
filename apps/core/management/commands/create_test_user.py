# apps/core/management/commands/create_test_user.py
"""
テストユーザー作成コマンド
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'テストユーザーを作成します'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='ユーザー名')
        parser.add_argument('--email', type=str, help='メールアドレス')
        parser.add_argument('--password', type=str, help='パスワード')
        parser.add_argument('--role', type=str, choices=['admin', 'manager', 'staff'], 
                          default='staff', help='役職')
        parser.add_argument('--superuser', action='store_true', help='スーパーユーザーとして作成')

    def handle(self, *args, **options):
        username = options['username'] or input('ユーザー名: ')
        email = options['email'] or input('メールアドレス: ')
        password = options['password'] or input('パスワード: ')
        role = options['role']
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'ユーザー "{username}" は既に存在します')
            )
            return
        
        user_data = {
            'username': username,
            'email': email,
            'role': role,
            'is_staff': options['superuser'] or role in ['admin', 'manager'],
            'is_superuser': options['superuser'],
        }
        
        user = User.objects.create_user(password=password, **user_data)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'ユーザー "{user.username}" を作成しました (役職: {user.get_role_display()})'
            )
        )