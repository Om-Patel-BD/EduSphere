from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
            null=True,
            blank=True
    )
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=20)
    semester = models.IntegerField(default=1)  # ✅ ADD THIS
    profile_image = models.ImageField(
    upload_to='profile_images/',
    null=True,
    blank=True
)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    semester = models.IntegerField(
        null=True,   # ✅ important (safe migration)
        blank=True
    )

    def __str__(self):
        return self.name
    
class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    subject_fk = models.ForeignKey(
            Subject,
            on_delete=models.CASCADE,
            null=True,
            blank=True
        )

    marks = models.IntegerField()
    semester = models.IntegerField()

    def __str__(self):
        return f"{self.student.name} - {self.subject_fk.name if self.subject_fk else 'No Subject'}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student.name} - {self.date}"
    


