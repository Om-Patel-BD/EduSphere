from django.urls import path
from . import admin_views
from . import teacher_views
from . import student_views
from . import shared_views

urlpatterns = [
    # ADMIN MODULE
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/students/', admin_views.admin_manage_students, name='admin_manage_students'),
    path('admin-dashboard/teachers/', admin_views.admin_manage_teachers, name='admin_manage_teachers'),
    path(
        'admin-dashboard/overview/',
        admin_views.admin_academic_attendance_overview,
        name='admin_academic_attendance_overview'
    ),
    path(
        'admin-dashboard/reports/',
        admin_views.admin_reports,
        name='admin_reports'
    ),
    path('admin-dashboard/assign-subjects/', admin_views.assign_subjects, name='assign_subjects'),


    # TEACHER MODULE
    path('teacher-dashboard/', teacher_views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/add-marks/', teacher_views.add_marks, name='add_marks'),
    path('teacher/attendance/', teacher_views.mark_attendance, name='mark_attendance'),
    path('teacher/profile/', teacher_views.teacher_profile, name='teacher_profile'),
    path(
        "teacher/delete-submission/<int:submission_id>/",
        teacher_views.delete_submission,
        name="delete_submission"
    ),
    path(
        "teacher/review-submission/<int:submission_id>/",
        teacher_views.mark_submission_reviewed,
        name="review_submission"
    ),
    path(
        "teacher/support/",
        teacher_views.teacher_support,
        name="teacher_support"
    ),
    path(
        'teacher/send-notification/',
        teacher_views.send_notification_page,
        name='send_notification_page'
    ),
    path(
        'teacher/get-students-by-subject/',
        teacher_views.get_students_by_subject,
        name='get_students_by_subject'
    ),


    # STUDENT MODULE
    path('student-dashboard/', student_views.student_dashboard, name='student_dashboard'),
    path('student/attendance/', student_views.student_attendance_history, name='student_attendance'),
    path('student/marks/', student_views.student_marks_details, name='student_marks'),
    path('student/profile/', student_views.student_profile, name='student_profile'),
    path('student/summary/', student_views.student_summary, name='student_summary'),
    path(
        'student/notifications/',
        student_views.student_notifications,
        name='student_notifications'
    ),
    path(
        'student/delete-notification/<int:notification_id>/',
        student_views.delete_notification,
        name='delete_notification'
    ),
    path(
        'student/materials/',
        student_views.student_materials,
        name='student_materials'
    ),
    path(
        'student/remove-material/<int:material_id>/',
        student_views.remove_material,
        name='remove_material'
    ),
    path(
        'student/submit-assignment/',
        student_views.student_submit_assignment,
        name='student_submit_assignment'
    ),
    path(
        "student/support/",
        student_views.student_support,
        name="student_support"
    ),


    # SHARED MODULE
    path('download-material/<int:material_id>/', shared_views.download_material, name='download_material'),
    path(
        'download-submission/<int:submission_id>/',
        shared_views.download_submission,
        name='download_submission'
    ),
]
