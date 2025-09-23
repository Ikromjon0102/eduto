from django.contrib import admin
from .models import User, Grade, Group, Course, Payment, Attendance, Room, MonthPeriod


class AdminUser(admin.ModelAdmin):
    list_display = ('username','full_name')


admin.site.register(MonthPeriod)
admin.site.register(User, AdminUser)
admin.site.register(Room)
admin.site.register(Grade)
admin.site.register(Group)
admin.site.register(Course)
admin.site.register(Payment)
admin.site.register(Attendance)