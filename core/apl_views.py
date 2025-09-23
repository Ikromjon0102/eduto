from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.views import View

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from .models import Applicant
from .forms import ApplicantCreateForm
from core.forms import GroupEditForm
from core.models import Group

User = get_user_model()


def applicant_list(request):
    applicants = User.objects.filter(role='applicant')  # Faqat applicantlarni olish
    return render(request, 'applicants/applicant_list.html', {'applicants': applicants})


class GroupEditView(View):
    def get(self, request, group_id):
        group = Group.objects.get(id = group_id)
        group_form = GroupEditForm(instance=group)
        students = User.objects.filter(Q(role='student',  group=group))

        context = {
            'group': group,
            'group_form':group_form,
            'students':students
        }
        return render(request, 'group/group_edit.html', context)


    def post(self, request, group_id):
        group = Group.objects.get(id=group_id)
        group_form = GroupEditForm(request.POST)
        if group_form.is_valid():
            group_form.save()
            return redirect(reverse('group_edit', kwargs={'group_id':group.id}))
        context = {
            'group': group,
            'group_form': group_form,
        }
        return render(request, 'group/group_edit.html', context)


class ApplicantCreateView(CreateView):
    model = Applicant
    form_class = ApplicantCreateForm
    template_name = "applicant_form.html"
    success_url = reverse_lazy('applicant_list')  # Applicantlar ro‘yxati sahifasi

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.user.set_password(self.object.user.password)  # Parolni hash qilib saqlash
        self.object.user.save()
        return response
