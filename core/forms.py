from django.db.models import Q
from django.forms import ModelForm
from django.urls import reverse_lazy


from .models import User, Course, Group, Payment, User, Applicant
from django import forms
from .models import Grade


class GroupEditForm(ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'course', 'teacher', 'schedule', 'room')



class UserCreateForm(ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'image')


    def save(self, commit=True):

        user = super().save(commit)
        user.username = self.cleaned_data['first_name'].lower() + '_' + self.cleaned_data['last_name'].lower()
        user.save()

        return user

class CourseCreateForm(ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
    
    def save(self, commit = True):
        course = super().save(commit)
        course.save()


from django import forms
from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from core.models import Group, User

class GroupCreateForm(ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(Q(role='applicant') | Q(role='student',  group=None)),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Applicantlarni tanlang"
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'dd-mm-yyyy'}),
        input_formats=['%d-%m-%Y']
    )

    class Meta:
        model = Group
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Saqlash", css_class="btn btn-primary"))

    def save(self, commit=True):
        group = super().save(commit=False)
        if commit:
            group.save()
            applicants = self.cleaned_data.get('students')
            for student in applicants:
                student.role = 'student'
                student.group = group
                student.save()
        return group

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['group', 'student', 'month_period', 'amount', 'comment', 'payment_method']
        widgets = {
            'group': forms.Select(attrs={
                'hx-get': reverse_lazy('load_students'),
                'hx-target': '#id_student',
                'hx-trigger': 'change'})}

        payment_method = forms.ChoiceField(
            choices=Payment.PAYMENT_METHODS,
            widget=forms.RadioSelect(attrs={'class': 'd-none'}),  # Asosiy inputni yashirish
            initial='cash'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].widget.attrs.update({
            'hx-get': reverse_lazy('load_students'),
            'hx-target': '#id_student',  # ID to'g'ri ekanligiga ishonch hosil qiling
            'hx-trigger': 'change'
        })
        self.fields['group'].label = "Guruh"
        self.fields['student'].label = "O'quvchi"
        self.fields['month_period'].label = "Oylik davr"
        self.fields['amount'].label = "To'lov summasi"
        self.fields['payment_method'].label = "To'lov usuli"
        self.fields['comment'].label = "Izoh"

        # Agar guruh tanlangan bo'lsa, o'quvchilar ro'yxatini filter qilish
        if 'group' in self.data:
            try:
                group_id = int(self.data.get('group'))
                self.fields['student'].queryset = User.objects.filter(
                    group_id=group_id,
                    role='student'
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.group:
            self.fields['student'].queryset = User.objects.filter(
                group=self.instance.group,
                role='student'
            )
        else:
            self.fields['student'].queryset = User.objects.none()

        # Bootstrap class larini qo'shish
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get('group')
        if group:
            cleaned_data['course'] = group.course
        return cleaned_data



class PaymentPersonalForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'comment']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }



class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'grade', 'comment', 'month_period']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


from django import forms
from .models import User, Applicant
from .validators import validate_phone_number

class ApplicantCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))  # Date picker
    phone_own = forms.CharField(
        max_length=15,
        validators=[validate_phone_number],
        help_text="Masalan: +998901234567"
    )
    phone_parents = forms.CharField(
        max_length=15,
        validators=[validate_phone_number],
        help_text="Masalan: +998901234567"
    )

    class Meta:
        model = Applicant
        fields = ['first_name', 'last_name', 'birth_date', 'phone_own', 'phone_parents', 'study_field', 'preferred_time']

    def save(self, commit=True):
        username = f"{self.cleaned_data['last_name']}{self.cleaned_data['first_name']}".lower()
        password = f"{username}2025"

        # Foydalanuvchi yaratish
        user = User.objects.create(
            username=username,  # Required field
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            role='applicant',
        )
        user.set_password(password)  # Parol o‘rnatish
        user.save()

        # Applicant obyektini yaratish
        applicant = super().save(commit=False)
        applicant.user = user
        if commit:
            applicant.save()
        return applicant
