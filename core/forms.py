
from django.forms import ModelForm
from django.urls import reverse_lazy

from .models import User, Course, Group, Payment, User
from django import forms
from .models import Grade

class UserCreateForm(ModelForm):
    class Meta:
        model = User
        fields = ('username', 'group', 'first_name', 'last_name', 'role', 'phone', 'image')


    def save(self, commit=True):
        user = super().save(commit)
        user.save()

        return user

class CourseCreateForm(ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
    
    def save(self, commit = True):
        course = super().save(commit)
        course.save()

class GroupCreateForm(ModelForm):
    class Meta:
        model = Group
        fields = '__all__'

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'dd-mm-yyyy'}),
        input_formats=['%d-%m-%Y']
    )

    def save(self, commit = True):
        return super().save(commit)

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