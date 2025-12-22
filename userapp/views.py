from ast import Return
from email.message import Message

# from ssl import _PasswordType
from django.db.models import Avg,Max,Min,Sum,Count,StdDev,Variance
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from adminapp.models import *
from mainapp.models import *
from userapp.models import *
import pytesseract
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# import imutils
import cv2
import os
from car_social_network.settings import DEFAULT_FROM_EMAIL
from django.core.mail import EmailMultiAlternatives
import requests
import pathlib
from django.core.files.storage import FileSystemStorage
import socket
from django.core.paginator import Paginator
# Create your views here.


def user_index(request):
    
    if request.method == "POST" and request.FILES["license"]:
        
        plate_img=request.FILES["license"]
        

        #License plate number is extracted from image here!
        # temp_img=ImgModel.objects.create(image=plate_img)
        # temp_img.save()
        
        pytesseract.pytesseract.tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'





        path=str(plate_img)
        

        image = cv2.imread('media/temp_img/'+path)
        
        # image resizing
        try:  
            resize = cv2.resize(  
                image, None, fx = 2, fy = 2,   
                interpolation = cv2.INTER_CUBIC) 
                
            
            # converting image to grayscale  
            gray = cv2.cvtColor(  
                resize, cv2.COLOR_BGR2GRAY)  
            
            # denoising the image  
            blur = cv2.GaussianBlur(  
                gray, (5, 5), 0) 


            #tesseract
            plate_number = pytesseract.image_to_string(blur, lang ='eng')  
            license_no = "".join(plate_number.split()).replace(":", "").replace("—", "").replace("|SS", "").replace("|", "").replace("Wea", "").replace("=»'", "").replace(")", "").replace("I", "").replace("_", "").replace("-", "").replace("(", "").replace("‘", "")
            


            try:
                driver = UserModel.objects.get(user_license= license_no) 
                
                # return redirect('user_index')
            except:
                messages.info(request, 'No Driver Found')
                return redirect('user_index')
            return render(request,"user/user-index.html",{'driver':driver})
        except:
            messages.info(request, 'No Driver Found With This Plate')
    return render(request,"user/user-index.html")


# def user_com(request):
#     if request.method =="POST":
#         message=request.POST.get("message")
#         print(message,"comm message")
#     return render(request,"user/user-com.html")


def user_interactions(request):
    user_id=request.session['user_id']
    my_inter = InteractionModel.objects.filter(from_user = user_id)
    paginator = Paginator(my_inter,5)
    page_no = request.GET.get('page')
    page = paginator.get_page(page_no)
    return render(request,"user/user-interactions.html",{'a':page})



def user_profile(request):
    user_id=request.session['user_id']
    user=UserModel.objects.get(user_id=user_id)
    # device=DeviceModel.objects.filter(device_user=user_id).count()

    
   from django.shortcuts import render, redirect
from django.contrib import messages
from userapp.models import UserModel


def home_user_reg(request):
    if request.method == "POST":
        try:
            # text fields
            name = request.POST.get("name")
            email = request.POST.get("email")
            password = request.POST.get("password")
            contact = request.POST.get("contact")
            visibal = request.POST.get("visibal")

            # checkboxes
            contact1 = request.POST.get("contact1")
            contact2 = request.POST.get("contact2")
            contact3 = request.POST.get("contact3")

            # files (SAFE access)
            license_img = request.FILES.get("license")
            photo = request.FILES.get("photo")

            # basic validation
            if not all([name, email, password, contact, visibal, license_img, photo]):
                messages.error(request, "All fields are required")
                return redirect("home_user_reg")

            # email uniqueness check
            if UserModel.objects.filter(user_email=email).exists():
                messages.error(request, "Email already registered")
                return redirect("home_user_reg")

            # save user (NO OCR, NO OPENCV)
            user = UserModel.objects.create(
                user_name=name,
                user_email=email,
                user_password=password,
                user_contact=contact,
                user_license=license_img,
                user_photo=photo,
                user_privacy_status=visibal,
                contact_email=contact1 is not None,
                contact_sms=contact2 is not None,
                contact_call=contact3 is not None,
                user_status="pending",
            )

            messages.success(request, "Registration successful. Await admin approval.")
            return redirect("home_user_login")

        except Exception as e:
            print("REGISTRATION ERROR:", e)
            messages.error(request, "Server error during registration")
            return redirect("home_user_reg")

    return render(request, "home/home-user-reg.html")
    
def user_feedback(request):
    user_id=request.session['user_id']
    user=UserModel.objects.get(user_id=user_id)
    if request.method == "POST":
        rating=request.POST.get("rating")
        review=request.POST.get("review")
        sid_obj= SentimentIntensityAnalyzer()
        sentinent = sid_obj.polarity_scores(review)
        
        if sentinent["compound"] > 0:
            sent = "positive"
        elif sentinent["compound"] < 0:
            sent = "negative"

        else:
            sent = "neutral"

        if sent:
            feedback = FeedbackModel.objects.create(review=review,rating=rating,reviewer=user,sentiment=sent)
            feedback.save()
            messages.success(request,"Your review has been added succesfully.")
            
            
            return redirect('user_feedback')

        else:
            
            messages.info(request,"You have already reviewed this driver.")
            return redirect('user_feedback')

       
    
    return render(request,"user/user-feedback.html")



def contact_email(request,driver_id,text):
    user_id=request.session['user_id']
    user=UserModel.objects.get(user_id=user_id)
    u1=user.user_id
    
    
    driver=UserModel.objects.get(user_id=driver_id)
    d1=driver.user_id
    if request.method =="POST":
        message = request.POST.get("message")
        
        if text == 'email':
            #email integration
            html_content = "<p>From:&nbsp;"+user.user_name+"</p>"+"<br>"+message+"."
            from_mail = DEFAULT_FROM_EMAIL

            to_mail = [driver.user_email]
            
            msg = EmailMultiAlternatives(
                "Car Social Network", html_content, from_mail, to_mail)
            msg.attach_alternative(html_content, "text/html")
            print(html_content,from_mail,to_mail,msg,'asdasdasdasdsdd')
            msg.send()
            if msg:
                InteractionModel.objects.create(message=message,interac_type =text,to_user=driver,from_user=user)
                print('ededededed')
                messages.success(request, 'Email Sent Successfully')
                return redirect('contact_email',driver_id=driver_id,text=text)
            
        elif text == 'sms':
            #SMS API CODE
                
                url = "https://www.fast2sms.com/dev/bulkV2"
                # create a dictionary
                my_data = {'sender_id': 'FSTSMS', 
                                'message': 'From '+user.user_name+','+message,
                                'language': 'english', 
                                'route': 'q', 
                                'numbers':8328035152,
                }
                
                    # create a dictionary
                headers = {
                        'authorization': "Ns8H1mKg294AjeBz5DMxLhPaZrbFR7tfpk3EX6wYJWUqd0noiGlHUTm1nDyEaCpx38R45MtKJg9kG6iB",
                        'Content-Type': "application/x-www-form-urlencoded",
                        'Cache-Control': "no-cache"
                }
                    # make a post request
                response = requests.request("POST",url,data = my_data,headers=headers)
                # print(response.text,"sms message")
                
                sms=InteractionModel.objects.create(message=message,interac_type =text,to_user=driver,from_user=user)
                messages.success(request, 'Sms Sent Successfully')

                
                return redirect('contact_email',driver_id=driver_id,text=text)
        

    return render(request,"user/user-com.html",{'driver':driver_id,'text':text})


def contact_call(request,driver_id,text):
    user_id=request.session['user_id']
    user=UserModel.objects.get(user_id=user_id)
    u1=user.user_id
    driver=UserModel.objects.get(user_id=driver_id)
    
    d1=driver.user_id

    
            #call integration
    calls=InteractionModel.objects.create(message="call",interac_type =text,to_user=driver,from_user=user)
    
    if calls:
    
        
        messages.success(request,"Call Made Successfully")
        return redirect('user_index')
    
    else:
        messages.error(request,"Something went wrong")
        return redirect('user_index')
    return render(request,"user/user-index.html")

# def contact_sms(request,driver_id,sms):
#     user_id=request.session['user_id']
#     user=UserModel.objects.get(user_id=user_id)
#     driver=UserModel.objects.get(user_id=driver_id)
#     if request.method =="POST":
#         message = request.POST.get("message")
#         print(message,"sms message")

    

    

#     return render(request,"user/user-com.html")

#review from user
# def review(request,driver_id):
#     user_id=request.session['user_id']
#     user=UserModel.objects.get(user_id=user_id)
#     driver=UserModel.objects.get(user_id=driver_id)
#     if  request.method=="POST":
#         rating = request.POST.get("rating")
#         review = request.POST.get("review")
#         sid_obj= SentimentIntensityAnalyzer()
#         sentinent = sid_obj.polarity_scores(review)
        
#         if sentinent["compound"] > 0:
#             sent = "positive"
#         elif sentinent["compound"] < 0:
#             sent = "negative"

#         else:
#             sent = "neutral"

#         try:
#             a=FeedbackModel.objects.get(reviewer=user_id,reviewee=driver_id)
#             messages.info(request,"You have already reviewed this driver.")
#             print(a)
#             return redirect('review',driver_id=driver_id)

#         except:
#             feedback = FeedbackModel.objects.create(review=review,rating=rating,reviewer=user,reviewee=driver,sentinent=sent)
#             feedback.save()
#             messages.success(request,"Your review has been added succesfully.")
#             return redirect('review',driver_id=driver_id)

#     return render(request,"user/user-feedback.html")