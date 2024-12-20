from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .forms import UserCreateForm, CourseCreateForm, GroupCreateForm, PaymentPersonalForm, PaymentForm
from .models import User, Group, Course

class Profile(View):

    def get(self, request):
        form1 = UserCreateForm()
        form2 = CourseCreateForm()
        form3 = GroupCreateForm()
        students = User.objects.filter(role='student')
        teachers = User.objects.filter(role='teacher')
        courses = Course.objects.all()
        groups = Group.objects.all()

        context = {
            'courses': courses,
            'groups': groups,
            'form_student': form1,
            'form_course': form2,
            'form_group': form3,
            'teachers': teachers,
            'students': students
        }
        return render(request, 'admin.html', context)

    def post(self, request):
        create_form = UserCreateForm(data=request.POST)
        create_course_form = CourseCreateForm(data=request.POST)
        create_group_form = GroupCreateForm(data=request.POST)
        if create_form.is_valid():
            create_form.save()
            return redirect('manager_page')

        elif create_course_form.is_valid():
            create_course_form.save()
            return redirect('manager_page')

        elif create_group_form.is_valid():
            create_group_form.save()
            return redirect('manager_page')
        else:
            context = {
                'form_student': create_form,
                'form_course': create_course_form,
                'form_group': create_group_form,
            }
            return render(request, 'admin.html', context)