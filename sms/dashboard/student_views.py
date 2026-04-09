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
from django.core.paginator import Paginator


# =========================
# STUDENT DASHBOARD
# =========================
@login_required
@role_required('student')
def student_dashboard(request):

    # Get logged-in student
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('login')  # or a custom "not linked" page


    # ---------- ATTENDANCE ----------
    total_att = Attendance.objects.filter(student=student).count()
    present_att = Attendance.objects.filter(
        student=student, status=True
    ).count()
    absent_att = Attendance.objects.filter(
        student=student, status=False
    ).count()

    attendance_percent = (
        (present_att / total_att) * 100 if total_att > 0 else 0
    )

    # ---------- MARKS ----------
    marks_qs = Mark.objects.select_related('subject_fk').filter(student=student)
    avg_marks = marks_qs.aggregate(avg=Avg('marks'))['avg'] or 0

    subjects = [m.subject_fk.name for m in marks_qs]
    marks = [m.marks for m in marks_qs]

    # ---------- ATTENDANCE TREND (LAST 7 DAYS) ----------
    from datetime import timedelta
    from django.utils.timezone import now

    trend_labels = []
    attendance_trend = []

    for i in range(6, -1, -1):
        day = now().date() - timedelta(days=i)
        trend_labels.append(day.strftime('%d %b'))

        present = Attendance.objects.filter(
            student=student, date=day, status=True
        ).count()
        attendance_trend.append(present)
        

    context = {
        'student': student,

        'attendance_percent': round(attendance_percent, 2),
        'present_att': present_att,
        'total_att': total_att,

        'avg_marks': round(avg_marks, 2),
        'subjects': subjects,
        'marks': marks,

        'attendance_trend_labels': trend_labels,
        'attendance_trend': attendance_trend,

        'absent_att': absent_att,
    }

    return render(request, 'student/dashboard.html', context)


@login_required
@role_required('student')
def student_summary(request):
    student = Student.objects.get(user=request.user)

    # ---------- ATTENDANCE ----------
    total_attendance = Attendance.objects.filter(student=student).count()
    present_attendance = Attendance.objects.filter(
        student=student, status=True
    ).count()
    absent_attendance = total_attendance - present_attendance

    attendance_percent = (
        (present_attendance / total_attendance) * 100
        if total_attendance > 0 else 0
    )

    # ---------- MARKS ----------
    marks_qs = Mark.objects.filter(student=student)

    avg_marks = marks_qs.aggregate(avg=Avg('marks'))['avg'] or 0
    total_marks = marks_qs.aggregate(total=Sum('marks'))['total'] or 0
    total_exams = marks_qs.count()

    max_marks = total_exams * 100   # assuming each exam = 100
    overall_percentage = (
        (total_marks / max_marks) * 100
        if max_marks > 0 else 0
    )

    # SUBJECT-WISE AVG (keep as before)
    subject_wise_marks = marks_qs.values('subject_fk__name').annotate(
        subject_avg=Avg('marks')
    )

    # ---------- PERFORMANCE CATEGORY ----------
    if avg_marks >= 80:
        performance_status = "Top Performer"
    elif avg_marks >= 60:
        performance_status = "Average"
    else:
        performance_status = "Needs Improvement"

    # ---------- ATTENDANCE CATEGORY ----------
    if attendance_percent >= 85:
        attendance_status = "Excellent"
    elif attendance_percent >= 70:
        attendance_status = "Good"
    else:
        attendance_status = "At Risk"

    # ---------- RISK DETECTION ----------
    risk_message = None

    if avg_marks < 50 and attendance_percent < 65:
        risk_message = "High Risk: Low marks & poor attendance"
    elif avg_marks < 50:
        risk_message = "Warning: Low academic performance"
    elif attendance_percent < 65:
        risk_message = "Warning: Poor attendance"

    # ---------- CONTEXT ----------
    context = {
        'student': student,

        # attendance
        'total_attendance': total_attendance,
        'present_attendance': present_attendance,
        'absent_attendance': absent_attendance,
        'attendance_percent': round(attendance_percent, 2),
        'attendance_status': attendance_status,

        # marks
        'avg_marks': round(avg_marks, 2),
        'total_marks': total_marks,
        'overall_percentage': round(overall_percentage, 2),
        'subject_wise_marks': subject_wise_marks,
        'performance_status': performance_status,

        # risk
        'risk_message': risk_message,
    }

    return render(request, 'student/summary.html', context)


@login_required
@role_required('student')
def student_attendance_history(request):
    student = Student.objects.get(user=request.user)

    records = Attendance.objects.filter(student=student).order_by('-date')

    return render(
        request,
        'student/attendance_history.html',
        {'records': records}
    )

@login_required
@role_required('student')
def student_materials(request):

    student = Student.objects.get(user=request.user)

    materials = StudyMaterial.objects.filter(
        recipients=student
    ).order_by('-created_at')

    return render(
        request,
        'student/materials.html',
        {'materials': materials}
    )

@login_required
@role_required('student')
def remove_material(request, material_id):

    student = Student.objects.get(user=request.user)

    material = StudyMaterial.objects.get(id=material_id)

    # Remove only this student from recipients
    material.recipients.remove(student)

    return redirect('student_materials')

@login_required
@role_required('student')
def student_marks_details(request):
    student = Student.objects.get(user=request.user)

    marks = Mark.objects.select_related('subject_fk').filter(student=student)

    return render(
        request,
        'student/marks_details.html',
        {'marks': marks}
    )


@login_required
@role_required('student')
def student_profile(request):

    student = get_object_or_404(Student, user=request.user)

    if request.method == 'POST':
        if request.FILES.get('profile_image'):
            student.profile_image = request.FILES['profile_image']
            student.save()

    # Delete existing image
        if request.POST.get('delete_image'):
            student.profile_image.delete(save=False)
            student.profile_image = None
            student.save()

    return render(request, 'student/profile.html', {
        'student': student
    })


@login_required
@role_required("student")
def student_support(request):

    student = Student.objects.get(user=request.user)
    teachers = Teacher.objects.all()
    teacher_id = request.GET.get("teacher")
    messages_list = []

    if teacher_id:
        teacher = Teacher.objects.get(id=teacher_id)

        # Mark teacher messages as seen by student
        SupportMessage.objects.filter(
            student=student,
            teacher=teacher,
            sender="teacher",
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
                sender="student",
                message=text
            )

            return redirect(f"/student/support/?teacher={teacher_id}")

    return render(
        request,
        "student/support.html",
        {
            "teachers": teachers,
            "messages_list": messages_list,
            "selected_teacher": teacher_id
        }
    )



# ================================
# STUDENT → VIEW NOTIFICATIONS
# ================================
@login_required
@role_required('student')
def student_notifications(request):
    student = Student.objects.get(user=request.user)

    notifications = Notification.objects.filter(
        recipients=student
    ).order_by('-created_at')

    return render(
        request,
        'student/notifications.html',
        {'notifications': notifications}
    )

# DELETE STUDENT NOTIFICATION

@login_required
@role_required('student')
def delete_notification(request, notification_id):
    student = Student.objects.get(user=request.user)

    notification = Notification.objects.get(id=notification_id)

    notification.recipients.remove(student)

    return redirect('student_notifications')


@login_required
@role_required('student')
def student_submit_assignment(request):

    student = Student.objects.get(user=request.user)

    my_submissions = StudentSubmission.objects.filter(
        student=student
    ).select_related("teacher").order_by("-submitted_at")

    teachers = Teacher.objects.all()

    if request.method == "POST":

        teacher_id = request.POST.get("teacher")
        message = request.POST.get("message")
        file = request.FILES.get("file")

        teacher = Teacher.objects.get(id=teacher_id)

        StudentSubmission.objects.create(
            student=student,
            teacher=teacher,
            file=file,
            message=message
        )

        messages.success(request, "Assignment submitted successfully.")

        return redirect("student_submit_assignment")

    return render(
        request,
        "student/submit_assignment.html",
        {
            "teachers": teachers,
            "my_submissions": my_submissions
        }
    )


