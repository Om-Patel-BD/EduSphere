from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from .models import Profile
from students.models import Student
from django.contrib import messages
import random
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from teachers.models import Teacher
import re


def register(request):
    if request.method == 'POST':
        # 1️⃣ Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')
        roll_no = request.POST.get('roll_no')

        # 2️⃣ Password validation
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long")
            return render(request, 'accounts/register.html')

        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least 1 uppercase letter")
            return render(request, 'accounts/register.html')

        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least 1 lowercase letter")
            return render(request, 'accounts/register.html')

        if not re.search(r'[0-9]', password):
            messages.error(request, "Password must contain at least 1 number")
            return render(request, 'accounts/register.html')

        if not re.search(r'[@$!%*?&.#_-]', password):
            messages.error(request, "Password must contain at least 1 special character")
            return render(request, 'accounts/register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'accounts/register.html')

        # 3️⃣ Username and email validation
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, 'accounts/register.html')

        # 4️⃣ Role-based validation
        if role == 'student' and not roll_no:
            messages.error(request, "Roll number is required for students")
            return render(request, 'accounts/register.html')

        # 5️⃣ Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # 6️⃣ Create Profile
        Profile.objects.create(
            user=user,
            role=role
        )

        # 7️⃣ AUTO-LINK STUDENT
        if role == 'student':
            try:
                student = Student.objects.get(
                    roll_no=roll_no,
                    user__isnull=True
                )
                student.user = user
                student.save()

            except Student.DoesNotExist:
                messages.error(
                    request,
                    "Invalid roll number or student already linked"
                )
                user.delete()
                return render(request, 'accounts/register.html')

        # 8️⃣ AUTO-LINK TEACHER
        if role == 'teacher':
            try:
                teacher = Teacher.objects.get(
                    email=email,
                    user__isnull=True
                )
                teacher.user = user
                teacher.save()

            except Teacher.DoesNotExist:
                messages.error(
                    request,
                    "No teacher record found with this email. Contact admin."
                )
                user.delete()
                return render(request, 'accounts/register.html')

        messages.success(request, "Registration successful. Please login.")
        return redirect('login')

    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            role = user.profile.role

            # =========================
            # STUDENT → OTP LOGIN
            # =========================
            if role == 'student':
                if not user.email:
                    messages.error(request, "Email not found. Contact admin.")
                    return redirect('login')

                otp = random.randint(100000, 999999)

                # store OTP in session
                request.session['otp'] = str(otp)
                request.session['otp_user_id'] = user.id

                # send OTP email
                from django.template.loader import render_to_string

                otp = random.randint(100000, 999999)

                request.session['otp'] = str(otp)
                request.session['otp_user_id'] = user.id

                html_content = render_to_string('accounts/otp_email.html', {
                    'otp': otp,
                    'username': user.username
                })

                email = EmailMultiAlternatives(
                    subject="Verify Your Login - EduSphere",
                    body=f"Your OTP is {otp}",   # fallback
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )

                email.attach_alternative(html_content, "text/html")
                email.send()

                return redirect('verify_otp')

            # ========================= 
            # ADMIN / TEACHER LOGIN
            # =========================
            else:
                login(request, user)

                if role == 'admin':
                    return redirect('admin_dashboard')
                elif role == 'teacher':
                    return redirect('teacher_dashboard')

        # =========================
        # INVALID LOGIN (IMPORTANT FIX)
        # =========================
        else:
            messages.error(request, "Invalid Username or Password")
            return redirect('login')   # 🔥 prevents resubmission popup

    # GET request
    return render(request, 'accounts/login.html')


def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')
        user_id = request.session.get('otp_user_id')

        if not session_otp or not user_id:
            messages.error(request, "Session expired. Please login again.")
            return redirect('login')

        if entered_otp == session_otp:
            user = User.objects.get(id=user_id)
            login(request, user)

            # cleanup
            request.session.pop('otp', None)
            request.session.pop('otp_user_id', None)

            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid OTP")
            return redirect('verify_otp')

    return render(request, 'accounts/verify_otp.html')



def logout_view(request):
    logout(request)
    return redirect('login')

def home(request):
    if request.user.is_authenticated:
        role = request.user.profile.role
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'student':
            return redirect('student_dashboard')
    return redirect('login')


