
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from loginPage import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokens import generate_token
from django.core.mail import EmailMessage, send_mail

# Create your views here.
def home(request):
    return render(request, "authentication/index.html")

def signup(request):

    if request.method == "POST":
        username = request.POST['username']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if User.objects.filter(username=username):
            messages.error(request, 'Username already exist!')
            return redirect('signup')

        if User.objects.filter(email = email):
            messages.error(request, 'Email already registered!')
            return redirect('signup')

        if len(username)>10:
            messages.error(request, 'Username must be under 10 characters')
            return redirect('signup')

        if password != confirm_password:
            messages.error(request, "Passwords don't match!")
            return redirect('signup')

        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!")
            return redirect('signup')

        myuser = User.objects.create_user(username, email, password)
        myuser.first_name = firstname
        myuser.last_name = lastname
        myuser.is_active = False
        myuser.save()

        messages.success(request, "Your Account has been successfully created. We have sent you a confirmation e-mail. Please confirm your e-mail in order to activate your account.")

        # Welcome Email

        subject = "Welcome to SynthalAI!!!"
        message = f"Hello {myuser.first_name}!!\nWelcome to SynthalAI!!\nThank You to visiting our website\nWe have also sent you a confirmation email, please confirm your email address in order to activate your account.\n\nThanking You\nDeepesh Gupta"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=False)

        # Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your email address to signup in SynthalAI"
        message2 = render_to_string('email_confirmation.html',{
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })

        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email]
        )
        email.fail_silently = True
        email.send()

        return redirect('signin')
        

    return render(request, "authentication/signup.html")

def signin(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user);
            first_name = user.first_name
            return render(request, "authentication/index.html", {'first_name': first_name})
        else:
            messages.error(request, "Invalid Username or Password!")
            return redirect('signin')

    return render(request, "authentication/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully")
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        first_name = myuser.first_name
        return redirect('home')
    else:
        return render(request, 'activation_failed.html')

