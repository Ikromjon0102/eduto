import re
from django.core.exceptions import ValidationError

def validate_phone_number(value):
    """Telefon raqamni faqat +998 bilan boshlanadigan formatda tekshirish"""
    pattern = r'^\+998\d{9}$'  # +998 bilan boshlanib, keyin 9 ta raqam bo‘lishi kerak
    if not re.match(pattern, value):
        raise ValidationError("Telefon raqam noto‘g‘ri formatda! Masalan: +998901234567")
