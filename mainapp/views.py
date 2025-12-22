from ast import Return
from email.message import Message
from itertools import count

from unicodedata import category
# from ssl import _PasswordType
from django.db.models import Avg,Max,Min,Sum,Count,StdDev,Variance
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from adminapp.models import *
from mainapp.models import *
from userapp.models import *
import pytesseract
import PIL.Image
# import imutils
import cv2
import os


# Create your views here.


def home_index(request):
    return render(request,"home/home-index.html")


def home_admin_login(request):
    if request.method == "POST":
        username=request.POST.get("username")
        password=request.POST.get("password")
        
        

        if username == "admin" and password == "admin":
            messages.success(request,'Successfully Login')
            return redirect('admin_index')
        else:
            messages.error(request,'invalid login credentials')
            return redirect('home_admin_login')
    return render(request,"home/home-admin-login.html")


def home_user_login(request):
    if request.method == "POST":
        username=request.POST.get("email")
        password=request.POST.get("password")
        

        try:
            # s1=UserModel.objects.filter(user_status="accepted") | UserModel.objects.filter(user_status="warned")
            auth = UserModel.objects.get(user_email=username,user_password=password)
            if auth.user_status  == "accepted":
                request.session['user_id'] = auth.user_id
                messages.success(request,'Successfully Logged In')
                return redirect('user_index')
            elif auth.user_status == "pending":
                messages.info(request,'Your id is pending for registration ')
                return redirect('home_user_login')
            elif auth.user_status == "blocked":
                messages.error(request,'You Are BLOCKED From Logging In ')
                return redirect('home_user_login')
            else:
                messages.error(request,'You are not registered,try again after signup')
                return redirect('home_user_login')
            
        except:
            messages.error(request,'invalid login credentials')
            return redirect('home_user_login')
    return render(request,"home/home-user-login.html")


from django.shortcuts import render, redirect
from django.contrib import messages
from userapp.models import UserModel

def home_user_reg(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name")
            email = request.POST.get("email")
            password = request.POST.get("password")
            contact = request.POST.get("contact")
            license_img = request.FILES.get("license")
            photo = request.FILES.get("photo")
            contact1 = request.POST.get("contact1")
            contact2 = request.POST.get("contact2")
            contact3 = request.POST.get("contact3")
            visibal = request.POST.get("visibal")

            if not all([name, email, password, contact, license_img, photo, visibal]):
                messages.error(request, "All fields are required")
                return redirect("home_user_reg")

            # create user
            user = UserModel.objects.create(
                user_name=name,
                user_email=email,
                user_password=password,
                user_contact=contact,
                user_license=license_img,   # FILE FIELD
                user_photo=photo,           # FILE FIELD
                user_privacy_status=visibal,
                user_status="pending"
            )

            messages.success(request, "Registration successful! Wait for admin approval.")
            return redirect("home_user_login")

        except Exception as e:
            print("REG ERROR:", e)
            messages.error(request, "Something went wrong")
            return redirect("home_user_reg")

    return render(request, "home/home-user-reg.html")


def about(request):
    return render(request,"home/about.html")