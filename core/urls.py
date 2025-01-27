from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import (Profile, generate_excel_report, generate_pdf_report,
                    import_from_excel, excel_page, UstozPorfileView,
                    PaymentView, PaymentCreateView, load_students,
                    group_details, StudentProfileView, PaymentPersonalView, PaymentHistoryView, PaymentUpdateView,
                    PaymentDeleteView, add_grade, teacher_students, teacher_groups, teacher_profile, get_group_students,
                    CustomLoginView, add_grade_profile, unpaid_students, StudentProfileForTeacherView,
                    download_template_with_data)



urlpatterns = [

    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('manager/', Profile.as_view(), name='manager_page'),

    path('teacher/profile/', teacher_profile, name='teacher_profile'),
    path('teacher/groups/', teacher_groups, name='teacher_groups'),
    path('teacher/students/', teacher_students, name='teacher_students'),
    path('teacher/add_grade/profile/', add_grade_profile, name='add_grade_profile'),
    path('teacher/add_grade/', add_grade, name='add_grade'),

    path('teacher/<int:ustoz_id>', UstozPorfileView.as_view(), name='teacher_page'),

    path('student/<int:student_id>/<int:row>', PaymentPersonalView.as_view(), name = 'per_payment'),

    path('payment/history/<int:pk>/', PaymentHistoryView.as_view(), name='payment_history'),
    path('payment/update/<int:pk>/', PaymentUpdateView.as_view(), name='payment_update'),
    path('payment/delete/<int:pk>/', PaymentDeleteView.as_view(), name='payment_delete'),

    path('student/<int:pk>/', StudentProfileView.as_view(), name='student_profile'),
    path('teacher-student/<int:pk>/', StudentProfileForTeacherView.as_view(), name='student_profile_for_teacher'),

    path('payments/add/', PaymentCreateView.as_view(), name='payment_add'),
    path('load-students/', load_students, name='load_students'),
    path('api/groups/<int:group_id>/', group_details, name='group_details'),

    # path('payment/add/', PaymentCreateView.as_view(), name='payment_add'),
    path('payments/', PaymentView.as_view(), name='payments'),
    path('load-students/', load_students, name='load_students'),

    # file export va import
    path('report/pdf/', generate_pdf_report, name='pdf_report'),
    path('report/excel/', generate_excel_report, name='excel_report'),
    path('import/excel/', import_from_excel, name='import_excel'),
    path('template/excel/', download_template_with_data, name='download_template_excel'),
    path('excel/import', excel_page, name='excel_page'),

    # modal uchun
    path('api/groups/<int:group_id>/payments/create/', PaymentView.as_view(), name='create_group_payments'),
    path('api/groups/<int:group_id>/students/', get_group_students, name='group_students_api'),
    path('api/unpaid-students/', unpaid_students, name='unpaid_students'),
]



