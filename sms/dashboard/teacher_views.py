from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from students.models import Student, Mark, Attendance, Subject
from teachers.models import Teacher
from dashboard.models import Notification, StudyMaterial, StudentSubmission, SupportMessage
from datetime import date, timedelta
from django.urls import reverse
from django.db.models import Avg, Sum, Count
from django.http import JsonResponse
from django.core.paginator import Paginator

# =========================
# TEACHER DASHBOARD
# =========================

@login_required
@role_required('teacher')
def teacher_dashboard(request):

    teacher = Teacher.objects.get(user=request.user)

    # =============================
    # BASIC SETUP
    # =============================
    today = date.today()
    active_section = request.POST.get('active_section') or request.GET.get('section', 'dashboard')
    student_filter = request.GET.get('student')
    subject_filter = request.GET.get('subject')
    sort_marks = request.GET.get('sort_marks')

# =============================
# STUDENTS WITHOUT ATTENDANCE (FOR MARK ATTENDANCE UI)
# =============================
    from datetime import datetime

    attendance_date_str = request.POST.get('attendance_date') or request.GET.get('attendance_date')

    # Safe date parsing
    if attendance_date_str:
        try:
            selected_attendance_date = datetime.strptime(attendance_date_str, "%Y-%m-%d").date()
        except:
            selected_attendance_date = today
    else:
        selected_attendance_date = today

    # Students already marked for selected date
    marked_student_ids = Attendance.objects.filter(
        date=selected_attendance_date
    ).values_list('student_id', flat=True)

    # Students NOT marked (to show checkboxes)
    students_unmarked = Student.objects.exclude(id__in=marked_student_ids)

    # Check if ALL students marked
    total_students_count = Student.objects.count()
    marked_count = Attendance.objects.filter(date=selected_attendance_date).count()
    all_marked = (marked_count == total_students_count)



    total_students = Student.objects.count()
    total_subjects = teacher.subjects.count()
    total_teachers = Teacher.objects.count()

    students = Student.objects.all()

    # ✅ Get teacher subjects
    teacher_subjects = teacher.subjects.all()

    # ✅ Filter marks
    all_marks = Mark.objects.select_related('student', 'subject_fk').filter(
        subject_fk__in=teacher_subjects
    )

    # =============================
    # MARKS FILTER + SORT
    # =============================

    # SUBJECT FILTER
    if subject_filter:
        all_marks = all_marks.filter(subject_fk_id=subject_filter)

    # STUDENT FILTER (Dropdown)
    if student_filter:
        all_marks = all_marks.filter(student_id=student_filter)

    # SORT
    if sort_marks == 'asc':
        all_marks = all_marks.order_by('marks')
    elif sort_marks == 'desc':
        all_marks = all_marks.order_by('-marks')

    # Subject list
    subjects_list = Subject.objects.filter(
    semester__in=Student.objects.values_list('semester', flat=True).distinct(),
    id__in=teacher.subjects.values_list('id', flat=True)
    )

    # Students list for dropdown
    students_list = Student.objects.only('id', 'name')

    if subject_filter or student_filter:
        marks_page_number = 1

    # =============================
    # PAGINATION - MANAGE MARKS
    # =============================
    marks_paginator = Paginator(all_marks, 10)  
    marks_page_number = request.GET.get('marks_page')
    marks_page_obj = marks_paginator.get_page(marks_page_number)

    # =============================
    # ATTENDANCE TODAY (COUNTS)
    # =============================
    today_attendance = Attendance.objects.filter(date=today)
    present_today = today_attendance.filter(status=True).count()
    absent_today = today_attendance.filter(status=False).count()
    marked_today = present_today + absent_today

    # =============================
    # WEEKLY / MONTHLY ATTENDANCE
    # =============================
    week_start = today - timedelta(days=7)
    monthly_start = today.replace(day=1)

    weekly_present = Attendance.objects.filter(date__gte=week_start, status=True).count()
    weekly_absent = Attendance.objects.filter(date__gte=week_start, status=False).count()

    monthly_present = Attendance.objects.filter(date__gte=monthly_start, status=True).count()
    monthly_absent = Attendance.objects.filter(date__gte=monthly_start, status=False).count()

    # =============================
    # MARKS DISTRIBUTION
    # =============================
    excellent = Mark.objects.filter(marks__gte=90).count()
    good = Mark.objects.filter(marks__range=(75, 89)).count()
    average = Mark.objects.filter(marks__range=(50, 74)).count()
    poor = Mark.objects.filter(marks__lt=50).count()

    # =============================
    # GRAPH DATA (ALWAYS DEFINED)
    # =============================
    total_attendance_records = Attendance.objects.count()
    present_records = Attendance.objects.filter(status=True).count()

    avg_attendance = (
        (present_records / total_attendance_records) * 100
        if total_attendance_records > 0 else 0
    )

    avg_marks_overall = Mark.objects.aggregate(avg=Avg('marks'))['avg'] or 0

    # =============================
    # DEFAULT VALUES (SAFE)
    # =============================
    selected_student = None
    student_marks = None
    student_attendance_percent = None

    attendance_records = None
    manage_attendance_records = None
    selected_date = None
    attendance_page_obj = None

    present_count_date = 0
    absent_count_date = 0
    total_records = 0
    attendance_percent_date = 0

    # =============================
    # POST HANDLING
    # =============================
    if request.method == 'POST':
        active_section = request.POST.get('active_section', 'dashboard')

        # VIEW STUDENT
        if 'view_student' in request.POST:
            selected_student = Student.objects.get(id=request.POST.get('student_id'))
            student_marks = Mark.objects.filter(student=selected_student)

            total_att = Attendance.objects.filter(student=selected_student).count()
            present_att = Attendance.objects.filter(
                student=selected_student, status=True
            ).count()

            student_attendance_percent = (
                (present_att / total_att) * 100 if total_att > 0 else 0
            )

        # ATTENDANCE BY DATE
        elif 'view_attendance_date' in request.POST:
            selected_date = request.POST.get('date')
            student_id = request.POST.get('student_id')

            searched_attendance_date = True

            if selected_date:
                # Selected student record (for table)
                attendance_records = Attendance.objects.select_related('student').filter(
                    student_id=student_id,
                    date=selected_date
                )

                # FULL DAY SUMMARY (for cards)
                all_day_records = Attendance.objects.filter(date=selected_date)

                total_records = all_day_records.count()
                present_count_date = all_day_records.filter(status=True).count()
                absent_count_date = all_day_records.filter(status=False).count()

                attendance_percent_date = (
                    (present_count_date / total_records) * 100
                    if total_records > 0 else 0
                )

        # MANAGE ATTENDANCE (VIEW)
        elif 'manage_attendance' in request.POST:
            active_section = 'manageAttendance'
            selected_date = request.POST.get('date')

            if selected_date:
                manage_attendance_records = Attendance.objects.select_related(
                    'student'
                ).filter(date=selected_date)


        # UPDATE ATTENDANCE
        elif 'update_attendance' in request.POST:
            active_section = 'manageAttendance'   # ⭐ FORCE TAB STAY
            selected_date = request.POST.get('selected_date')

            Attendance.objects.filter(
                id=request.POST.get('attendance_id')
            ).update(
                status=request.POST.get('status') == 'present'
            )

            if selected_date:
                manage_attendance_records = Attendance.objects.select_related(
                    'student'
                ).filter(date=selected_date)                                

        # DELETE ATTENDANCE
        elif 'delete_attendance' in request.POST:
            active_section = 'manageAttendance'   # ⭐ FORCE TAB STAY
            selected_date = request.POST.get('selected_date')

            Attendance.objects.filter(
                id=request.POST.get('attendance_id')
            ).delete()

            if selected_date:
                manage_attendance_records = Attendance.objects.select_related(
                    'student'
                ).filter(date=selected_date)

        # EDIT MARKS
        elif 'edit_mark' in request.POST:
            Mark.objects.filter(
                id=request.POST.get('mark_id')
            ).update(
                marks=request.POST.get('marks')
            )

        # DELETE MARKS
        elif 'delete_mark' in request.POST:
            mark_id = request.POST.get('delete_mark')
            Mark.objects.filter(id=mark_id).delete()

        # =============================
        # DELETE STUDY MATERIAL (TEACHER)
        # =============================
        elif "delete_material" in request.POST:

            material_id = request.POST.get("material_id")

            material = StudyMaterial.objects.get(
                id=material_id,
                uploaded_by=teacher   # security check
            )

            # Delete file from storage
            material.file.delete(save=False)

            # Delete record
            material.delete()


        # =============================
        # BULK UPDATE MARKS
        # =============================
        elif 'bulk_update' in request.POST:

            mark_ids = request.POST.getlist('mark_ids')

            for mark_id in mark_ids:
                new_marks = request.POST.get(f'marks_{mark_id}')

                if new_marks:
                    Mark.objects.filter(id=mark_id).update(
                        marks=new_marks
                    )

        # DELETE SELECTED
        elif 'delete_selected' in request.POST:

            active_section = 'manageAttendance'   # ✅ stay on same tab
            selected_date = request.POST.get('selected_date')

            ids = request.POST.getlist('delete_ids')
            Attendance.objects.filter(id__in=ids).delete()

            # ✅ reload same date records
            if selected_date:
                manage_attendance_records = Attendance.objects.select_related(
                    'student'
                ).filter(date=selected_date)

        # BULK ATTENDANCE
        elif 'bulk_attendance_update' in request.POST:

            selected_date = request.POST.get('selected_date')

            attendance_records = Attendance.objects.filter(date=selected_date)

            for record in attendance_records:
                new_status = request.POST.get(f'status_{record.id}')

                if new_status:
                    record.status = True if new_status == 'present' else False
                    record.save()



    # =============================
    # LOAD MANAGE ATTENDANCE FROM GET (PAGINATION SUPPORT)
    # =============================
    attendance_date_get = request.GET.get('attendance_date')

    if attendance_date_get and request.GET.get('section') == 'manageAttendance':
        active_section = 'manageAttendance'
        selected_date = attendance_date_get

        queryset = Attendance.objects.select_related('student').filter(
            date=selected_date
        )
    
    if selected_date:
        manage_attendance_records = Attendance.objects.select_related(
            'student'
        ).filter(date=selected_date)

    
    # =============================
    # STUDY MATERIALS (TEACHER)
    # =============================

    teacher = Teacher.objects.get(user=request.user)

    # Upload material
    if request.method == "POST" and "upload_material" in request.POST:
        title = request.POST.get("title")
        description = request.POST.get("description")
        file = request.FILES.get("file")
        selected_students = request.POST.getlist("students")

        material = StudyMaterial.objects.create(
            title=title,
            description=description,
            file=file,
            uploaded_by=teacher
        )

        if selected_students:
            material.recipients.set(selected_students)
        else:
            material.recipients.set(Student.objects.all())

    # Fetch teacher materials
    teacher_materials = StudyMaterial.objects.filter(
        uploaded_by=teacher
    ).order_by("-created_at")

    # =============================
    # STUDENT ASSIGNMENT SUBMISSIONS
    # =============================

    teacher_submissions = StudentSubmission.objects.filter(
        teacher=teacher
    ).select_related("student").order_by("-submitted_at")


    


    # =============================
    # CONTEXT
    # =============================
    context = {
        'active_section': active_section,

        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_teachers': total_teachers,

        'present_today': present_today,
        'absent_today': absent_today,
        'marked_today': marked_today,
                 
        'present_count': present_today,
        'absent_count': absent_today,
        'weekly_present': weekly_present,
        'weekly_absent': weekly_absent,
        'monthly_present': monthly_present,
        'monthly_absent': monthly_absent,

        'excellent': excellent,
        'good': good,
        'average': average,
        'poor': poor,

        'avg_attendance': round(avg_attendance, 2),
        'avg_marks_overall': round(avg_marks_overall, 2),

        'students': students,
        'students_unmarked': students_unmarked,
        'attendance_form_date': selected_attendance_date,
        'all_marked': all_marked,

        'all_marks': marks_page_obj,
        'marks_page_obj': marks_page_obj,

        'selected_student': selected_student,
        'student_marks': student_marks,
        'student_attendance_percent': (
            round(student_attendance_percent, 2)
            if student_attendance_percent is not None else None
        ),

        'attendance_records': attendance_records,
        'manage_attendance_records': manage_attendance_records,
        'selected_date': selected_date,

        'today_date': today.isoformat(),
        'students_list': students_list,
        'student_filter': student_filter,
        'subjects_list': subjects_list,
        'subject_filter': subject_filter,   
        'attendance_page_obj': attendance_page_obj,

        'present_count_date': present_count_date if attendance_records else 0,
        'absent_count_date': absent_count_date if attendance_records else 0,
        'total_records_date': total_records if attendance_records else 0,
        'attendance_percent_date': round(attendance_percent_date, 2) if attendance_records else 0,
        'searched_attendance_date': searched_attendance_date if 'searched_attendance_date' in locals() else False,

        'teacher_materials': teacher_materials,
        'teacher_submissions': teacher_submissions,
        'teacher_subjects': teacher.subjects.all(),
    }

    return render(request, 'teacher/dashboard.html', context)

@login_required
@role_required("teacher")
def delete_submission(request, submission_id):

    submission = StudentSubmission.objects.get(id=submission_id)

    submission.file.delete(save=False)

    submission.delete()

    messages.success(request, "Submission deleted successfully")

    return redirect("teacher_dashboard")

@login_required
@role_required("teacher")
def mark_submission_reviewed(request, submission_id):

    submission = StudentSubmission.objects.get(id=submission_id)

    submission.status = "reviewed"
    submission.save()

    return redirect("/teacher-dashboard/?section=submissions")

@login_required
@role_required('teacher')
def teacher_profile(request):
    
    teacher = get_object_or_404(Teacher, user=request.user)

    # Handle avatar upload
    if request.method == 'POST':
        if request.FILES.get('profile_image'):
            teacher.profile_image = request.FILES['profile_image']
            teacher.save()

    # Delete image
        if request.POST.get('delete_image'):
            teacher.profile_image.delete(save=False)
            teacher.profile_image = None
            teacher.save()

    return render(
        request,
        'teacher/profile.html',
        {'teacher': teacher}
    )

@login_required
@role_required("teacher")
def teacher_support(request):

    teacher = Teacher.objects.get(user=request.user)
    students = Student.objects.all()
    student_id = request.GET.get("student")
    messages_list = []

    if student_id:
        student = Student.objects.get(id=student_id)

        # Mark student messages as seen by teacher
        SupportMessage.objects.filter(
            student=student,
            teacher=teacher,
            sender="student",
            is_seen=False
        ).update(is_seen=True)

        messages_list = SupportMessage.objects.filter(
            student=student,
            teacher=teacher
        ).order_by("sent_at")

        if request.method == "POST":
            text = request.POST.get("message")

            SupportMessage.objects.create(
                student=student,
                teacher=teacher,
                sender="teacher",
                message=text
            )

            return redirect(f"/teacher/support/?student={student_id}")

    return render(
        request,
        "teacher/support.html",
        {
            "students": students,
            "messages_list": messages_list,
            "selected_student": student_id
        }
    )


# =========================
# TEACHER: ADD MARKS
# =========================
@login_required
@role_required('teacher')
def add_marks(request):

    teacher = Teacher.objects.get(user=request.user)

    if request.method == 'POST':

        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        marks = request.POST.get('marks')

        from students.models import Student, Subject

        student = Student.objects.get(id=student_id)
        subject = Subject.objects.get(id=subject_id)

        # 🔥 Security 1: Teacher subject check
        if not teacher.subjects.filter(id=subject.id).exists():
            return redirect('teacher_dashboard')

        # 🔥 Security 2: Semester match check
        if subject.semester != student.semester:
            return redirect('teacher_dashboard')

        Mark.objects.create(
            student=student,
            subject_fk=subject,
            marks=marks,
            semester=student.semester
        )

    return redirect('/teacher-dashboard/?section=addMarks')

# =========================
# TEACHER: MARK ATTENDANCE (DATE-WISE & SAFE)
# =========================

@login_required
@role_required('teacher')
def mark_attendance(request):
    if request.method == 'POST':

        attendance_date = request.POST.get('attendance_date')
        status = request.POST.get('status')
        student_ids = request.POST.getlist('student_ids')

        if not attendance_date or not status or not student_ids:
            return redirect(
                reverse('teacher_dashboard') +
                f'?section=attendance&attendance_date={attendance_date}'
            )

        for student_id in student_ids:
            Attendance.objects.update_or_create(
                student_id=student_id,
                date=attendance_date,
                defaults={'status': status == 'present'}
            )

    return redirect(
        reverse('teacher_dashboard') +
        f'?section=attendance&attendance_date={attendance_date}'
    )


# ================================
# TEACHER → SEND NOTIFICATION
# ================================
@login_required
@role_required('teacher')
def send_notification_page(request):
    students = Student.objects.all()

    if request.method == 'POST':
        teacher = get_object_or_404(Teacher, user=request.user)

        selected_students = request.POST.getlist('students')

        notification = Notification.objects.create(
            title=request.POST.get('title'),
            message=request.POST.get('message'),
            sender=teacher
        )

        # If no student selected → send to ALL
        if selected_students:
            notification.recipients.set(selected_students)
        else:
            notification.recipients.set(students)

        return redirect('teacher_dashboard')

    return render(
        request,
        'teacher/send_notification.html',
        {'students': students}
    )


from django.http import JsonResponse
from students.models import Student, Subject

@login_required
@role_required('teacher')
def get_students_by_subject(request):
    subject_id = request.GET.get('subject_id')

    try:
        subject = Subject.objects.get(id=subject_id)
        students = Student.objects.filter(semester=subject.semester)

        marked_students = Mark.objects.filter(
            subject_fk=subject
        ).values_list('student_id', flat=True)

        data = [
            {
                "id": s.id,
                "name": s.name,
                "marked": s.id in marked_students
            }
            for s in students
        ]

        return JsonResponse({
            "students": data,
            "semester": subject.semester
        })

    except:
        return JsonResponse({"students": [], "semester": None})


