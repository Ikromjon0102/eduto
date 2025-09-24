from .forms import ApplicantCreateForm, CourseCreateForm, GroupCreateForm, UserCreateForm

def sidebar_forms(request):
    return {
        "form_student": ApplicantCreateForm(),
        "form_course": CourseCreateForm(),
        "form_group": GroupCreateForm(),
        "form_teacher": UserCreateForm(),
    }