from django.db import models
from django.contrib.auth.models import User
from students.models import Subject


class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,      # allow existing rows
        blank=True      # allow admin to create without user
    )

    name = models.CharField(max_length=100)

    email = models.EmailField(
        unique=True,    # IMPORTANT for auto-link
        null=True,
        blank=True
    )

    subject = models.CharField(max_length=100)

    subjects = models.ManyToManyField(Subject, blank=True)

    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
