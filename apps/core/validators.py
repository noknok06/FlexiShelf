
"""
基本バリデーター
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_positive_float(value):
    """正の浮動小数点数のバリデーション"""
    if value <= 0:
        raise ValidationError(_('値は0より大きい必要があります。'))


def validate_positive_integer(value):
    """正の整数のバリデーション"""
    if value <= 0:
        raise ValidationError(_('値は0より大きい必要があります。'))


def validate_dimension(value):
    """寸法（cm）のバリデーション"""
    if value <= 0:
        raise ValidationError(_('寸法は0cmより大きい必要があります。'))
    if value > 1000:
        raise ValidationError(_('寸法は1000cm以下である必要があります。'))


def validate_face_count(value):
    """フェース数のバリデーション"""
    if value < 1:
        raise ValidationError(_('フェース数は1以上である必要があります。'))
    if value > 50:
        raise ValidationError(_('フェース数は50以下である必要があります。'))