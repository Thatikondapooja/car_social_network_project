import re
import cv2
import numpy as np
import pytesseract
import requests

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import EmailMultiAlternatives

from car_social_network.settings import DEFAULT_FROM_EMAIL
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from adminapp.models import *
from mainapp.models import *
from userapp.models import *


# =============================
# UTIL: Normalize license plate
# =============================
def normalize_plate(text):
    if not text:
        return ""

    text = text.upper()
    text = re.sub(r'[^A-Z0-9]', '', text)

    # OCR common corrections
    text = text.replace('O', '0')
    text = text.replace('I', '1')
    text = text.replace('Z', '2')

    return text


# =============================
# USER HOME / CONNECT PAGE
# =============================
def user_index(request):
    if request.method == "POST" and request.FILES.get("license"):
        try:
            plate_img = request.FILES["license"]

            # Tesseract path for Render (Linux)
            pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

            image = cv2.imdecode(
                np.frombuffer(plate_img.read(), np.uint8),
                cv2.IMREAD_COLOR
            )

            if image is None:
                raise ValueError("Image decode failed")

            resize = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(resize, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)

            raw_text = pytesseract.image_to_string(
                blur,
                config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )

            license_no = normalize_plate(raw_text)
            print("OCR RAW:", raw_text)
            print("OCR CLEAN:", license_no)

            if not license_no:
                messages.error(request, "Unable to read license plate")
                return redirect("user_index")

            driver = UserModel.objects.filter(
                user_license__iexact=license_no,
                user_status="accepted"
            ).first()

            if not driver:
                messages.info(request, "No Driver Found With This Plate")
                return redirect("user_index")

            return render(request, "user/user-index.html", {"driver": driver})

        except Exception as e:
            print("OCR ERROR:", e)
            messages.error(request, "Unable to read license plate")
            return redirect("user_index")

    return render(request, "user/user-index.html")


# =============================
# USER INTERACTIONS
# =============================
def user_interactions(request):
    user_id = request.session.get("user_id")
    interactions = InteractionModel.objects.filter(from_user=user_id)
    paginator = Paginator(interactions, 5)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "user/user-interactions.html", {"a": page})


# =============================
# USER PROFILE
# =============================
def user_profile(request):
    user_id = request.session.get("user_id")
    user = UserModel.objects.get(user_id=user_id)

    if request.method == "POST":
        user.user_name = request.POST.get("name")
        user.user_email = request.POST.get("email")
        user.user_password = request.POST.get("password")
        user.user_contact = request.POST.get("contact")
        user.user_privacy_status = request.POST.get("privacy")
        user.user_license = request.POST.get("license")

        if request.FILES.get("file"):
            user.user_photo = request.FILES["file"]

        user.save()
        messages.success(request, "Profile updated successfully")
        return redirect("user_profile")

    return render(request, "user/user-profile.html", {"user": user})


# =============================
# USER FEEDBACK
# =============================
def user_feedback(request):
    user_id = request.session.get("user_id")
    user = UserModel.objects.get(user_id=user_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        review = request.POST.get("review")

        sid = SentimentIntensityAnalyzer()
        score = sid.polarity_scores(review)["compound"]

        sentiment = "neutral"
        if score > 0:
            sentiment = "positive"
        elif score < 0:
            sentiment = "negative"

        FeedbackModel.objects.create(
            reviewer=user,
            rating=rating,
            review=review,
            sentiment=sentiment
        )

        messages.success(request, "Feedback submitted")
        return redirect("user_feedback")

    return render(request, "user/user-feedback.html")


# =============================
# CONTACT EMAIL / SMS
# =============================
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
                interac_type=text,
                to_user=driver,
                from_user=user,
            )

            messages.success(request, "Email sent successfully")

    return render(request, "user/user-com.html", {"driver": driver, "text": text})


# =============================
# CONTACT CALL
# =============================
def contact_call(request, driver_id, text):
    user = UserModel.objects.get(user_id=request.session["user_id"])
    driver = UserModel.objects.get(user_id=driver_id)

    InteractionModel.objects.create(
        message="call",
        interac_type=text,
        to_user=driver,
        from_user=user,
    )

    messages.success(request, "Call recorded successfully")
    return redirect("user_index")
