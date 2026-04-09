from django.db import models
from teachers.models import Teacher
from students.models import Student


class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    sender = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # NEW → who receives this notification
    recipients = models.ManyToManyField(
        Student,
        blank=True
    )

    def __str__(self):
        return self.title


class StudyMaterial(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    file = models.FileField(upload_to='study_materials/')

    uploaded_by = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE
    )

    recipients = models.ManyToManyField(
        Student,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    @property
    def safe_file_size(self):
        try:
            return self.file.size
        except Exception:
            return None

class StudentSubmission(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE
    )

    file = models.FileField(upload_to='student_submissions/')

    message = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("reviewed", "Reviewed")
        ],
        default="pending"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} submission"

    @property
    def safe_file_size(self):
        try:
            return self.file.size
        except Exception:
            return None
class SupportMessage(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE
    )

    sender = models.CharField(
        max_length=10,
        choices=[
            ("student", "Student"),
            ("teacher", "Teacher")
        ]
    )

    message = models.TextField()

    sent_at = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.name} → {self.teacher.name}"

