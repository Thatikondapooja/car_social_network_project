import re
import cv2
import numpy as np
import pytesseract
import requests

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import EmailMultiAlternatives

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from adminapp.models import *
from mainapp.models import *
from userapp.models import *
from car_social_network.settings import DEFAULT_FROM_EMAIL


# ==========================
# OCR HELPERS
# ==========================
def normalize_plate(text):
    if not text:
        return ""

    text = text.upper()
    text = re.sub(r'[^A-Z0-9]', '', text)

    text = text.replace('O', '0')
    text = text.replace('I', '1')
    text = text.replace('Z', '2')

    return text


# ==========================
# USER INDEX (CONNECT)
# ==========================
def user_index(request):
    if request.method == "POST" and request.FILES.get("license"):
        try:
            plate_img = request.FILES["license"]

            # Local vs Render tesseract path
            pytesseract.pytesseract.tesseract_cmd = (
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if os.name == "nt"
                else "/usr/bin/tesseract"
            )

            image = cv2.imdecode(
                np.frombuffer(plate_img.read(), np.uint8),
                cv2.IMREAD_COLOR
            )

            if image is None:
                raise ValueError("Invalid image")

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)

            plate_text = pytesseract.image_to_string(
                blur,
                config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )

            license_no = normalize_plate(plate_text)
            print("OCR PLATE:", license_no)

            if not license_no:
                messages.error(request, "Unable to read license plate")
                return redirect("user_index")

            driver = UserModel.objects.filter(
                user_license__icontains=license_no,
                user_status="accepted"
            ).first()

            if not driver:
                messages.info(request, "No Driver Found With This Plate")
                return redirect("user_index")

            return render(request, "user/user-index.html", {"driver": driver})

        except Exception as e:
            print("OCR ERROR:", e)
            messages.error(request, "Unable to read license plate")

    return render(request, "user/user-index.html")


# ==========================
# USER INTERACTIONS
# ==========================
def user_interactions(request):
    user_id = request.session.get("user_id")
    my_inter = InteractionModel.objects.filter(from_user=user_id)
    paginator = Paginator(my_inter, 5)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "user/user-interactions.html", {"a": page})


# ==========================
# USER PROFILE
# ==========================
def user_profile(request):
    user = UserModel.objects.get(user_id=request.session["user_id"])

    if request.method == "POST":
        user.user_name = request.POST.get("name")
        user.user_email = request.POST.get("email")
        user.user_password = request.POST.get("password")
        user.user_contact = request.POST.get("contact")
        user.user_privacy_status = request.POST.get("privacy")
        user.user_license = request.POST.get("license")

        if request.FILES.get("photo"):
            user.user_photo = request.FILES["photo"]

        user.save()
        messages.success(request, "Profile updated successfully")
        return redirect("user_profile")

    return render(request, "user/user-profile.html", {"user": user})


# ==========================
# USER FEEDBACK
# ==========================
def user_feedback(request):
    user = UserModel.objects.get(user_id=request.session["user_id"])

    if request.method == "POST":
        review = request.POST.get("review")
        rating = request.POST.get("rating")

        sid = SentimentIntensityAnalyzer()
        score = sid.polarity_scores(review)["compound"]

        sentiment = "positive" if score > 0 else "negative" if score < 0 else "neutral"

        FeedbackModel.objects.create(
            review=review,
            rating=rating,
            reviewer=user,
            sentiment=sentiment,
        )

        messages.success(request, "Feedback submitted")
        return redirect("user_feedback")

    return render(request, "user/user-feedback.html")


# ==========================
# CONTACT EMAIL / SMS
# ==========================
def contact_email(request, driver_id, text):
    user = UserModel.objects.get(user_id=request.session["user_id"])
    driver = UserModel.objects.get(user_id=driver_id)

    if request.method == "POST":
        message = request.POST.get("message")

        if text == "email":
            html = f"<p>From: {user.user_name}</p><br>{message}"
            msg = EmailMultiAlternatives(
                "Car Social Network",
                html,
                DEFAULT_FROM_EMAIL,
                [driver.user_email],
            )
            msg.attach_alternative(html, "text/html")
            msg.send()

            InteractionModel.objects.create(
                message=message,
                interac_type="email",
                to_user=driver,
                from_user=user,
            )

            messages.success(request, "Email sent")
            return redirect("user_index")

    return render(request, "user/user-com.html", {"driver": driver, "text": text})


# ==========================
# CONTACT CALL
# ==========================
def contact_call(request, driver_id, text):
    user = UserModel.objects.get(user_id=request.session["user_id"])
    driver = UserModel.objects.get(user_id=driver_id)

    InteractionModel.objects.create(
        message="call",
        interac_type="call",
        to_user=driver,
        from_user=user,
    )

    messages.success(request, "Call recorded successfully")
    return redirect("user_index")
