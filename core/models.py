from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models


# Foydalanuvchi modeli
class User(AbstractUser):
    ROLES = [
        ('manager', 'Manager'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('', 'Yangi'),
    ]
    role = models.CharField(max_length=10, choices=ROLES, default='student')
    phone = models.CharField(max_length=15, null=True, blank=True)
    image = models.ImageField(default='profile.png')
    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='users')


    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def full_name(self):
        return f'{self.last_name} {self.first_name}'

    def get_role_display(self):
        return self.role

    def total_groups(self):
        # Ustozning jami guruhlar sonini hisoblash
        return self.teaching_groups.count()

    def total_students(self):
        # Ustozning jami o'quvchilar sonini hisoblash
        return User.objects.filter(group__teacher=self, role='student').count()


class MonthPeriod(models.Model):
    start_date = models.DateField()  # Oyning boshlanish sanasi (masalan, 1-yanvar 2025)
    end_date = models.DateField()    # Oyning tugash sanasi (masalan, 31-yanvar 2025)
    name = models.CharField(max_length=50)  # Oy nomi (masalan, "Yanvar 2025")
    is_active = models.BooleanField(default=True)  # Aktiv davr yoki yo'q

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100)  # Kurs nomi (masalan, "Frontend")
    description = models.TextField(null=True, blank=True)  # Kurs haqida qisqacha ma'lumot
    duration_months = models.IntegerField()  # Kurs davomiyligi (oylar hisobida)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=0)  # Oylik to'lov

    def __str__(self):
        return self.name

class Room(models.Model):
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class Group(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'}, related_name='teaching_groups')
    name = models.CharField(max_length=100)  # Guruh nomi (masalan, "Frontend-1")
    start_date = models.DateField()  # Kurs boshlanish sanasi
    end_date = models.DateField(editable=False)  # Kurs tugash sanasi (avtomatik hisoblanadi)
    schedule = models.CharField(max_length=50, choices=[
        ('MWF1', 'Dushanba-Chorshanba-Juma (8:00-10:00)'),
        ('MWF2', 'Dushanba-Chorshanba-Juma (10:00-12:00)'),
        ('MWF3', 'Dushanba-Chorshanba-Juma (13:30-15:30)'),
        ('MWF4', 'Dushanba-Chorshanba-Juma (15:30-17:30)'),
        ('TTS1', 'Seshanba-Payshanba-Shanba (8:00-10:00)'),
        ('TTS2', 'Seshanba-Payshanba-Shanba (10:00-12:00)'),
        ('TTS3', 'Seshanba-Payshanba-Shanba (13:30-15:30)'),
        ('TTS4', 'Seshanba-Payshanba-Shanba (15:30-17:30)'),
    ])
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)  # Xona

    def save(self, *args, **kwargs):
        # Kurs davomiyligi asosida tugash sanasini avtomatik hisoblash
        if not self.end_date:
            self.end_date = self.start_date + relativedelta(months=self.course.duration_months)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.course.name})"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Naqd pul'),
        ('bank_transfer', 'Pul o\'tkazish'),
        ('card', 'Karta orqali'),
        ('payment_system', 'To\'lov tizimlari'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # Guruh
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    month_period = models.ForeignKey(MonthPeriod, on_delete=models.CASCADE, default=1)  # Oylik davr
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # To'lov summasi
    status = models.CharField(max_length=20, choices=[('paid', "To'langan"), ('unpaid', "To'lanmagan")], default='unpaid')
    date = models.DateField(auto_now_add=True)  # To'lov sanasi
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')  # To'lov turi
    comment = models.CharField(max_length=100, blank=True, null=True)  # Tranzaksiya ID (to'lov tizimlari uchun)

    def __str__(self):
        return f"{self.student.username} - {self.group.name} - {self.month_period.name} ({self.status})"


class Attendance(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # Guruh
    month_period = models.ForeignKey(MonthPeriod, on_delete=models.CASCADE, default=1)  # Oylik davr
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    is_present = models.BooleanField(default=False)  # Keldi/Kelmadi

    def __str__(self):
        return f"{self.student.username} - {self.group.name} - {self.month_period.name} ({'Keldi' if self.is_present else 'Kelmadi'})"


class Grade(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grades')
    month_period = models.ForeignKey(MonthPeriod, on_delete=models.CASCADE, default=1)  # Oylik davr
    grade = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])  # Baho
    comment = models.TextField(blank=True, null=True)  # Izoh
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_grades')  # Ustoz

    def __str__(self):
        return f"{self.student.username} - {self.grade} ({self.month_period.name})"


class Exam(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # Guruh
    month_period = models.ForeignKey(MonthPeriod, on_delete=models.CASCADE, default=1)  # Oylik davr
    max_score = models.DecimalField(max_digits=5, decimal_places=2)  # Maksimal ball

    def __str__(self):
        return f"{self.group.name} - {self.group.course.name} ({self.month_period.name})"

