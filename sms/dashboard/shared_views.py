from django.shortcuts import render, redirect, get_object_or_404
from .models import StudyMaterial, StudentSubmission
from django.http import FileResponse, Http404
import os

def download_material(request, material_id):
    material = StudyMaterial.objects.get(id=material_id)

    try:
        file_path = material.file.path
        if not os.path.exists(file_path):
            raise Http404("File not found.")
        file_name = os.path.basename(file_path)
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    except ValueError:
        raise Http404("File not found.")

def download_submission(request, submission_id):
    submission = StudentSubmission.objects.get(id=submission_id)

    try:
        file_path = submission.file.path
        if not os.path.exists(file_path):
            raise Http404("File not found.")
        file_name = os.path.basename(file_path)
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    except ValueError:
        raise Http404("File not found.")
