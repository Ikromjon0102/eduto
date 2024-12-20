from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count
from datetime import date
import openpyxl
from django.http import HttpResponse, JsonResponse
from reportlab.pdfgen import canvas
from django.views import View
from .models import *
from .forms import UserCreateForm, CourseCreateForm, GroupCreateForm, PaymentPersonalForm, PaymentForm
from .models import User, Group, Course
from django.views.generic import ListView, CreateView
from django.utils import timezone
from datetime import datetime
from .models import Payment


class Profile(View):

    def get(self, request):
        form1 = UserCreateForm()
        form2 = CourseCreateForm()
        form3 = GroupCreateForm()
        students = User.objects.filter(role = 'student')
        teachers = User.objects.filter(role = 'teacher')
        courses = Course.objects.all()
        groups = Group.objects.all()

        context = {
            'courses': courses,
            'groups': groups,
            'form_student': form1,
            'form_course': form2,
            'form_group': form3,
            'teachers':teachers,
            'students': students
        }
        return render(request, 'admin.html', context )


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




class UstozPorfileView(View):
    def get(self, request, ustoz_id):
        ustoz = User.objects.get(id=ustoz_id)
        groups = Group.objects.filter(teacher=ustoz)

        # Har bir guruhda o'quvchilarni filtrlash (faqat studentlar)
        groups_with_students = []
        for group in groups:
            students = group.users.filter(role='student')
            groups_with_students.append({'group': group, 'students': students})

        context = {
            'teacher': ustoz,
            'groups_with_students': groups_with_students
        }
        return render(request, 'teacher_page.html', context)


def generate_pdf_report(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="student_report.pdf"'

    # PDF fayl yaratish
    p = canvas.Canvas(response)
    p.drawString(100, 800, "Guruh va O'quvchilar Hisoboti")

    students = User.objects.filter(role='student')
    y = 750
    for student in students:
        p.drawString(100, y, f"{student.username} - {student.group}")
        y -= 20

    p.showPage()
    p.save()
    return response


def generate_excel_report(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="student_report.xlsx"'

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "O'quvchilar Hisoboti"

    # Sarlavhalar
    sheet.append(["Username", "Ism", "Guruh", ])

    students = User.objects.filter(role='student')
    for student in students:
        # student.group.name orqali guruhning nomini olish
        group_name = student.group.name if student.group else "Noma'lum"
        sheet.append([student.username, student.first_name, group_name])

    workbook.save(response)
    return response

def import_from_excel(request):

    # print(request)
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']

        # Excel faylini o'qish
        wb = openpyxl.load_workbook(excel_file)
        sheet = wb['jami']  # Bu yerda 'jami' sheet nomi bo'lishi kerak

        for row in sheet.iter_rows(min_row=2, values_only=True):  # Min row 2dan boshlab ma'lumotni o'qiydi
            first_name, last_name, course_id, group_id, teacher_id, phone = row

            # Kursni ID orqali olish
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                course = None  # Agar kurs topilmasa, uni None qilib qo'yish

            # Guruhni ID orqali olish
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                group = None  # Agar guruh topilmasa, uni None qilib qo'yish

            # Ustozni ID orqali olish
            try:
                teacher = User.objects.get(id=teacher_id, role='teacher')
            except User.DoesNotExist:
                teacher = None  # Agar ustoz topilmasa, uni None qilib qo'yish

            # User modelini yaratish
            if course and group and teacher:  # Agar barcha bog'lanishlar to'g'ri bo'lsa
                user = User.objects.create(
                    username = f"{first_name.lower()}_{last_name.lower()}",
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role='student',
                    group=group
                )
                user.save()
            else:
                # Agar biron narsa noto'g'ri bo'lsa, xabarni chiqaring
                print(f"User for {first_name} {last_name} not created due to missing relationships")

        # Import jarayoni tugagach, foydalanuvchini manager_page sahifasiga yo'naltirish
        return redirect('manager_page')  # 'manager_page' URL to'g'ri ekanligiga ishonch hosil qiling

    return render(request, 'upload.html')  # Agar POST bo'lmasa, formani ko'rsatish

def excel_page(request):
    return render(request, 'payment.html')




class PaymentView(ListView):
    model = Payment
    template_name = 'payment.html'
    context_object_name = 'payments'

    def get_queryset(self):
        # Barcha to'lovlarni olish
        queryset = Payment.objects.all().order_by('student', 'month')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Joriy sana
        today = timezone.now().date()
        # Joriy oyning 10-sanasi
        payment_deadline = datetime(today.year, today.month, 10).date()

        # To'lovlar uchun status
        payment_status = []
        for payment in context['payments']:
            # To'lov oyining 10-sanasi
            payment_month = datetime(payment.date.year, payment.date.month, 10).date()

            # Agar to'lov 'unpaid' va joriy sana 10-sanadan o'tgan bo'lsa
            is_overdue = payment.status == 'unpaid' and today > payment_month

            payment_status.append({
                'payment': payment,
                'is_overdue': is_overdue
            })

        context['payment_status'] = payment_status
        return context


class PaymentCreateView(View):
    template_name = 'payment_form.html'

    def get(self, request):
        # GET so'rovi uchun - formani ko'rsatish
        initial_data = {}

        # URL dan group_id kelgan bo'lsa
        group_id = request.GET.get('group')
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                initial_data = {
                    'group': group,
                    'amount': group.course.price_per_month,
                    'course': group.course
                }
            except Group.DoesNotExist:
                pass

        form = PaymentForm(initial=initial_data)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        # POST so'rovi uchun - formani saqlash
        form = PaymentForm(request.POST)

        if form.is_valid():
            try:
                # Guruhdan kursni olish
                payment = form.save(commit=False)
                payment.course = payment.group.course
                payment.status = 'paid'
                payment.save()

                messages.success(request, "To'lov muvaffaqiyatli qo'shildi!")
                return redirect('payments')
            except Exception as e:
                messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

        return render(request, self.template_name, {'form': form})


def load_students(request):
    """Guruh bo'yicha o'quvchilarni yuklash uchun AJAX view"""
    group_id = request.GET.get('group')
    if group_id:
        students = User.objects.filter(group_id=group_id, role='student')
        return JsonResponse({
            'students': [{'id': student.id, 'name': student.get_full_name() or student.username}
                         for student in students]
        })
    return JsonResponse({'students': []})


def group_details(request, group_id):
    """Guruh va kurs ma'lumotlarini olish uchun API view"""
    try:
        group = Group.objects.get(id=group_id)
        data = {
            'course': {
                'id': group.course.id,
                'price_per_month': float(group.course.price_per_month)
            }
        }
        return JsonResponse(data)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)


# views.py



class StudentProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'students/profile.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        if student.group:
            context['course'] = student.group.course
            context['start_date'] = student.group.start_date
            context['end_date'] = student.group.end_date

            # Hozirgi o'qiyotgan oyi
            start_date = student.group.start_date
            today = date.today()
            months_studied = relativedelta(today, start_date).months + 1
            context['current_month'] = min(months_studied, student.group.course.duration_months)

            # Kurs davomiyligi bo'yicha to'lovlar ro'yxati
            duration = student.group.course.duration_months
            payments = Payment.objects.filter(
                student=student,
                group=student.group
            ).order_by('month')

            # To'lovlar lug'atini yaratish
            payments_dict = {payment.month: payment for payment in payments}

            # Barcha oylar uchun to'lovlar ro'yxati
            all_payments = []
            monthly_payment = student.group.course.price_per_month

            for month in range(1, duration + 1):
                if month in payments_dict:
                    payment = payments_dict[month]
                    all_payments.append({
                        'month': month,
                        'amount': payment.amount,
                        'date': payment.date,
                        'status': payment.status,
                        'comment': payment.comment
                    })
                else:
                    all_payments.append({
                        'month': month,
                        'amount': monthly_payment,
                        'date': None,
                        'status': 'unpaid',
                        'comment': None
                    })

            context['all_payments'] = all_payments

            # Umumiy to'langan summa
            total_paid = payments.filter(
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or 0
            context['total_paid'] = total_paid

            # Baholar
            context['grades'] = Grade.objects.filter(student=student).order_by('-date')

            # O'rtacha baho
            if context['grades'].exists():
                avg_grade = sum(grade.grade for grade in context['grades']) / context['grades'].count()
                context['average_grade'] = round(avg_grade, 1)

        return context


# class PaymentPersonalView(View):
#     def get(self, request, student_id, row):
#         form = PaymentPersonalForm()
#
#         context = {
#             'form':form
#         }
#         return render(request, 'payment_personal.html', context)
#
#     def post(self, request, student_id, row):
#         student = User.objects.get(id = student_id)
#
#         form = PaymentPersonalForm(request.POST)
#         if form.is_valid():
#             payment = form.save(commit=False)
#             payment.course = student.group.course
#             payment.student = student
#             payment.group = student.group
#             payment.month = row
#             payment.status = 'paid'
#             payment.save()
#         return redirect('student_profile', pk = student_id )

# class PaymentPersonalView(LoginRequiredMixin, View):
#     def post(self, request, student_id, row):
#         try:
#             student = get_object_or_404(User, id=student_id)
#
#             # Studentning guruhi va kursi borligini tekshirish
#             if not student.group:
#                 messages.error(request, "O'quvchi hech qaysi guruhga biriktirilmagan!")
#                 return redirect('student_profile', pk=student_id)
#
#             form = PaymentPersonalForm(request.POST)
#             if form.is_valid():
#                 payment = form.save(commit=False)
#                 # Avval kursni o'rnatamiz
#                 payment.course = student.group.course
#                 payment.student = student
#                 payment.group = student.group
#                 payment.month = row
#                 payment.status = 'paid'
#
#                 # Kurs narxini tekshirish
#                 if payment.amount < payment.course.price_per_month:
#                     messages.error(
#                         request,
#                         f"To'lov summasi kurs narxidan ({payment.course.price_per_month}) kam bo'lmasligi kerak!"
#                     )
#                     return redirect('student_profile', pk=student_id)
#
#                 # Oldin to'lanmaganligini tekshirish
#                 if Payment.objects.filter(
#                         student=student,
#                         group=student.group,
#                         month=row,
#                         status='paid'
#                 ).exists():
#                     messages.error(request, f"{row}-oy uchun to'lov allaqachon amalga oshirilgan!")
#                     return redirect('student_profile', pk=student_id)
#
#                 payment.save()
#                 messages.success(request, f"{row}-oy uchun to'lov muvaffaqiyatli amalga oshirildi!")
#             else:
#                 messages.error(request, "Form to'ldirishda xatolik. Iltimos qaytadan urinib ko'ring.")
#
#         except Exception as e:
#             messages.error(request, f"Xatolik yuz berdi: {str(e)}")
#
#         return redirect('student_profile', pk=student_id)


class PaymentPersonalView(LoginRequiredMixin, View):
    def post(self, request, student_id, row):
        # try:
            print(f"Received POST request: student_id={student_id}, row={row}")
            print(f"POST data: {request.POST}")

            student = get_object_or_404(User, id=student_id)

            if not student.group:
                messages.error(request, "O'quvchi hech qaysi guruhga biriktirilmagan!")
                return redirect('student_profile', pk=student_id)

            form = PaymentPersonalForm(request.POST)

            # print(f"saaaaaalom, Form is valid: {form.is_valid()}")
            # if not form.is_valid():
            #     print(f"Form errors: {form.errors}")

            if form.is_valid():
                print('shu yerda xatolik')
                payment = form.save(commit=False)
                payment.course = student.group.course
                payment.student = student
                payment.group = student.group
                payment.month = row
                payment.status = 'paid'

                try:
                    payment.full_clean()
                    payment.save()
                    messages.success(request, f"{row}-oy uchun to'lov muvaffaqiyatli amalga oshirildi!")
                except ValidationError as e:
                    messages.error(request, f"Validatsiya xatosi: {e}")
                    return redirect('student_profile', pk=student_id)
            else:
                messages.error(request, f"Form xatosi: {form.errors}")

        # except Exception as e:
        #     print(f"Exception occurred: {str(e)}")
        #     messages.error(request, f"Xatolik yuz berdi: {str(e)}")

            return redirect('student_profile', pk=student_id)


class PaymentHistoryView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'payments/history.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        # To'lovlar statistikasi
        stats = Payment.objects.filter(student=student).aggregate(
            total_paid=Sum('amount', filter=models.Q(status='paid')),
            total_payments=Count('id', filter=models.Q(status='paid')),
            avg_payment=models.Avg('amount', filter=models.Q(status='paid'))
        )

        context.update({
            'payments': Payment.objects.filter(student=student).order_by('-date'),
            'stats': stats
        })

        return context


class PaymentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Payment
    form_class = PaymentPersonalForm
    template_name = 'payments/update.html'

    def test_func(self):
        # Faqat manager va teacher lar to'lovni tahrirlashi mumkin
        return self.request.user.role in ['manager', 'teacher']

    def get_success_url(self):
        return reverse('student_profile', kwargs={'pk': self.object.student.id})


class PaymentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Payment
    template_name = 'payments/delete.html'

    def test_func(self):
        # Faqat manager va teacher lar to'lovni o'chirishi mumkin
        return self.request.user.role in ['manager', 'teacher']

    def get_success_url(self):
        return reverse('student_profile', kwargs={'pk': self.object.student.id})