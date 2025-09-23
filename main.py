import os
import django

# Django sozlamalarini belgilash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Endi Django modellaridan foydalanishingiz mumkin
from core.models import User

users_without_password = User.objects.filter(password='')
for user in users_without_password:
    user.set_password('manager123')
    user.save()

print(f"{users_without_password.count()} ta foydalanuvchiga parol muvaffaqiyatli o'rnatildi!")
