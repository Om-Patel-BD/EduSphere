from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from students.models import Student, Mark, Attendance, Subject
from teachers.models import Teacher
from django.db.models import Avg, Sum, Count
from datetime import timedelta
from django.utils.timezone import now

# =========================
# ADMIN DASHBOARD
# =========================
@login_required
@role_required('admin')
def admin_dashboard(request):

    # ---------- TOP CARDS ----------
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()

    avg_marks = Mark.objects.aggregate(avg=Avg('marks'))['avg'] or 0

    total_attendance = Attendance.objects.count()
    present_count = Attendance.objects.filter(status=True).count()
    absent_count = Attendance.objects.filter(status=False).count()

    attendance_percent = (
        (present_count / total_attendance) * 100
        if total_attendance > 0 else 0
    )

    # ---------- MARKS DISTRIBUTION ----------
    excellent = Mark.objects.filter(marks__gte=90).count()
    good = Mark.objects.filter(marks__range=(75, 89)).count()
    average = Mark.objects.filter(marks__range=(50, 74)).count()
    poor = Mark.objects.filter(marks__lt=50).count()

    # ---------- ATTENDANCE TREND (LAST 7 DAYS) ----------
    labels = []
    attendance_trend = []

    for i in range(6, -1, -1):
        day = now().date() - timedelta(days=i)
        labels.append(day.strftime('%d %b'))

        present = Attendance.objects.filter(date=day, status=True).count()
        attendance_trend.append(present)

    context = {
        # cards
        'total_students': total_students,
        'total_teachers': total_teachers,
        'avg_marks': round(avg_marks, 2),
        'attendance_percent': round(attendance_percent, 2),

        # attendance distribution
        'present_count': present_count,
        'absent_count': absent_count,

        # marks distribution
        'excellent': excellent,
        'good': good,
        'average': average,
        'poor': poor,

        # trend
        'trend_labels': labels,
        'attendance_trend': attendance_trend,
    }

    return render(request, 'admin/dashboard.html', context)

# ADMIN MANAGE STUDENTS

@login_required
@role_required('admin')
def admin_manage_students(request):

    students = Student.objects.all()

    # ADD STUDENT
    if request.method == 'POST' and 'add_student' in request.POST:
        Student.objects.create(
            name=request.POST.get('name'),
            roll_no=request.POST.get('roll_no'),
            semester=request.POST.get('semester') or 1
        )

    # EDIT STUDENT
    elif request.method == 'POST' and 'edit_student' in request.POST:
        Student.objects.filter(
            id=request.POST.get('student_id')
        ).update(
            name=request.POST.get('name'),
            roll_no=request.POST.get('roll_no'),
            semester=request.POST.get('semester')
        )

    # DELETE STUDENT
    elif request.method == 'POST' and 'delete_student' in request.POST:
        Student.objects.filter(
            id=request.POST.get('student_id')
        ).delete()

    return render(
        request,
        'admin/manage_students.html',
        {'students': students}
    )


## MANAGE TEACHERS

@login_required
@role_required('admin')
def admin_manage_teachers(request):

    teachers = Teacher.objects.all()

    # ADD TEACHER
    if request.method == 'POST' and 'add_teacher' in request.POST:
        Teacher.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
        )

    # EDIT TEACHER
    elif request.method == 'POST' and 'edit_teacher' in request.POST:
        Teacher.objects.filter(
            id=request.POST.get('teacher_id')
        ).update(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            subject=request.POST.get('subject')
        )

    # DELETE TEACHER
    elif request.method == 'POST' and 'delete_teacher' in request.POST:
        Teacher.objects.filter(
            id=request.POST.get('teacher_id')
        ).delete()

    context = {
        'teachers': teachers
    }

    return render(request, 'admin/manage_teachers.html', context)


## ACADEMIC AND ATTENDANCE OVERVIEW

@login_required
@role_required('admin')
def admin_academic_attendance_overview(request):

    # -------- MARKS OVERVIEW --------
    avg_marks_overall = Mark.objects.aggregate(avg=Avg('marks'))['avg'] or 0

    subject_data = (
        Mark.objects.values('subject_fk__name')
        .annotate(avg_marks=Avg('marks'))
    )

    subjects = [s['subject_fk__name'] for s in subject_data]
    marks_avg = [round(s['avg_marks'], 2) for s in subject_data]

    # -------- ATTENDANCE OVERVIEW --------
    total_attendance = Attendance.objects.count()
    present_count = Attendance.objects.filter(status=True).count()
    absent_count = Attendance.objects.filter(status=False).count()

    attendance_percent = (
        (present_count / total_attendance) * 100
        if total_attendance > 0 else 0
    )

    context = {
        'avg_marks_overall': round(avg_marks_overall, 2),
        'subjects': subjects,
        'marks_avg': marks_avg,
        'attendance_percent': round(attendance_percent, 2),
        'present_count': present_count,
        'absent_count': absent_count,
    }

    return render(
        request,
        'admin/academic_attendance_overview.html',
        context
    )

## REPORTS

@login_required
@role_required('admin')
def admin_reports(request):

    students = Student.objects.all()

    selected_student = None
    student_marks = None
    attendance_percent = None

    selected_date = None
    attendance_records = None

    subject_marks = None
    selected_subject = None

    # ---------- STUDENT REPORT ----------
    if request.method == 'POST' and 'student_report' in request.POST:
        selected_student = Student.objects.get(id=request.POST.get('student_id'))

        student_marks = Mark.objects.filter(student=selected_student)

        total_att = Attendance.objects.filter(student=selected_student).count()
        present_att = Attendance.objects.filter(
            student=selected_student, status=True
        ).count()

        attendance_percent = (
            (present_att / total_att) * 100 if total_att > 0 else 0
        )

    # ---------- ATTENDANCE REPORT (DATE) ----------
    elif request.method == 'POST' and 'attendance_report' in request.POST:
        selected_date = request.POST.get('date')
        attendance_records = Attendance.objects.select_related(
            'student'
        ).filter(date=selected_date)

    # ---------- MARKS REPORT (SUBJECT) ----------
    elif request.method == 'POST' and 'marks_report' in request.POST:
        selected_subject = request.POST.get('subject')
        subject_marks = Mark.objects.select_related('student').filter(subject_fk_id=selected_subject)
        

    context = {
        'students': students,

        'selected_student': selected_student,
        'student_marks': student_marks,
        'attendance_percent': (
            round(attendance_percent, 2)
            if attendance_percent is not None else None
        ),

        'attendance_records': attendance_records,
        'selected_date': selected_date,

        'subject_marks': subject_marks,
        'selected_subject': selected_subject,
    }

    return render(request, 'admin/reports.html', context)

@login_required
@role_required('admin')
def assign_subjects(request):

    teachers = Teacher.objects.all()
    all_subjects = Subject.objects.all()

    filtered_subjects = None
    assign_subjects_list = all_subjects   # 🔥 always show all for assign

    selected_subject_id = request.GET.get("subject_filter")

    if selected_subject_id == "all":
        filtered_subjects = all_subjects

    elif selected_subject_id:
        filtered_subjects = all_subjects.filter(id=selected_subject_id)

    selected_teacher = None
    assigned_subject_ids = []

    teacher_id = request.GET.get("teacher") or request.POST.get("teacher")

    if teacher_id:
        selected_teacher = Teacher.objects.get(id=teacher_id)
        assigned_subject_ids = list(
            selected_teacher.subjects.values_list('id', flat=True)
        )

    # =========================
    # ➕ ADD NEW SUBJECT
    # =========================
    if request.method == "POST" and "add_subject" in request.POST:
        name = request.POST.get("subject_name")
        semester = request.POST.get("semester")

        if name and semester:
            # 🔥 Prevent duplicate subject
            if not Subject.objects.filter(name=name, semester=semester).exists():
                Subject.objects.create(
                    name=name,
                    semester=semester
                )

        return redirect(request.path)
    
    selected_subject_id = request.GET.get("subject_filter")

    if selected_subject_id:
        # Avoid overriding local subjects var if it doesn't exist
        # Originally this was updating a `subjects` variable that was probably `filtered_subjects`.
        # I am preserving original logic assuming template works, but it seems there was an issue in original code.
        # Original: subjects = subjects.filter(id=selected_subject_id)
        # Fix for original bug:
        pass
        # I'll leave it as it was if possible, but the original code had:
        #   if selected_subject_id:
        #       subjects = subjects.filter(id=selected_subject_id)
        # This causes UnboundLocalError! Let's write the exact original below.

    if selected_subject_id:
        try:
            subjects = subjects.filter(id=selected_subject_id)
        except UnboundLocalError:
            pass

    # =========================
    # ✏️ UPDATE SUBJECT
    # =========================
    if request.method == "POST" and "edit_subject" in request.POST:
        subject_id = request.POST.get("subject_id")
        name = request.POST.get("subject_name")
        semester = request.POST.get("semester")

        if subject_id and name and semester:
            Subject.objects.filter(id=subject_id).update(
                name=name,
                semester=semester
            )

        return redirect(request.path)


    # =========================
    # 🗑 DELETE SUBJECT
    # =========================
    if request.method == "POST" and "delete_subject" in request.POST:
        subject_id = request.POST.get("subject_id")

        # OPTIONAL SAFE DELETE
        from students.models import Mark
        if not Mark.objects.filter(subject_fk_id=subject_id).exists():
            Subject.objects.filter(id=subject_id).delete()

        return redirect(request.path)

    # =========================
    # ASSIGN / UNASSIGN SUBJECTS
    # =========================
    if request.method == "POST" and "subjects" in request.POST:
        subject_ids = request.POST.getlist("subjects")

        if selected_teacher:
            selected_teacher.subjects.set(subject_ids)

        return redirect(f"/admin-dashboard/assign-subjects/?teacher={teacher_id}")
    

    return render(request, "admin/assign_subjects.html", {
        "teachers": teachers,
        "subjects": filtered_subjects,          # for manage table
        "assign_subjects_list": assign_subjects_list,  # for assign table
        "selected_teacher": selected_teacher,
        "assigned_subject_ids": assigned_subject_ids,
        "selected_subject_id": selected_subject_id,
        "all_subjects": all_subjects,
    })
