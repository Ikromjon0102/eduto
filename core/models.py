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
    ]
    role = models.CharField(max_length=10, choices=ROLES, default='student')
    phone = models.CharField(max_length=15, null=True, blank=True)
    image = models.ImageField(default='profile.png')
    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='users')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_role_display(self):
        return self.role

    def total_groups(self):
        # Ustozning jami guruhlar sonini hisoblash
        return self.teaching_groups.count()

    def total_students(self):
        # Ustozning jami o'quvchilar sonini hisoblash
        return User.objects.filter(group__teacher=self, role='student').count()


# Kurs modeli
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    duration_months = models.IntegerField()
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    def total_price(self):
        return self.duration_months * self.price_per_month


# Guruh modeli
class Group(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='groups')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'},
                                related_name='teaching_groups')
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(editable=False)
    schedule = models.CharField(max_length=50, choices=[
                                        ('MWF1', 'Mon-Wed-Fri-8-10'),
                                        ('MWF2', 'Mon-Wed-Fri-10-12'),
                                        ('MWF3', 'Mon-Wed-Fri-13-15'),
                                        ('MWF4', 'Mon-Wed-Fri-15-17'),
                                        ('TTS1', 'Tue-Thu-Sat-8-10'),
                                        ('TTS2', 'Tue-Thu-Sat-10-12'),
                                        ('TTS3', 'Tue-Thu-Sat-13-15'),
                                        ('TTS4', 'Tue-Thu-Sat-15-17'),
                                        ('6days1', 'Mon-Sat1'),
                                        ('6days2', 'Mon-Sat2'),
                                        ('6days3', 'Mon-Sat3'),
                                        ('6days4', 'Mon-Sat4')])

    def save(self, *args, **kwargs):
        # Kurs muddati asosida tugash sanasini avtomatik hisoblash
        if not self.end_date:
            self.end_date = self.start_date + relativedelta(months=self.course.duration_months)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} {self.name} ({self.course.name})"

    def student_count(self):
        # Guruhdagi o'quvchilar sonini hisoblash
        return self.users.count()


class Payment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.PositiveIntegerField(verbose_name="To'lov oyi", default=1)
    comment = models.TextField(blank=True, null=True, verbose_name="Izoh")
    status = models.CharField(max_length=20, choices=[('paid', "To'langan"), ('unpaid', "To'lanmagan")],
                              default='unpaid')
    date = models.DateField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-date', 'student']

    def __str__(self):
        return f"{self.student.username} - {self.group.name} - {self.month}-oy ({self.status})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# Davomat modeli
class Attendance(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date = models.DateField()
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    is_present = models.BooleanField(default=False)

# Baholar modeli
class Grade(models.Model):
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='grades')
    date = models.DateField(auto_now_add=True)
    grade = models.IntegerField(choices=[
        (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')
    ], null=True, blank=True)
    comment = models.TextField(blank=True, null=True)
    teacher = models.ForeignKey('User', on_delete=models.CASCADE, related_name='given_grades', null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.username} - {self.grade} ({self.date})"


