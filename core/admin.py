from django.contrib import admin
from .models import User, Grade, Group, Course, Payment, Attendance, Room

admin.site.register(User)
admin.site.register(Room)
admin.site.register(Grade)
admin.site.register(Group)
admin.site.register(Course)
admin.site.register(Payment)
admin.site.register(Attendance)