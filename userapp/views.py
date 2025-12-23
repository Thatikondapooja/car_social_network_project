import re
import os
import cv2
import numpy as np

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import EmailMultiAlternatives

from car_social_network.settings import DEFAULT_FROM_EMAIL
from userapp.models import UserModel, InteractionModel, FeedbackModel

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests


# -------------------------------
# Utility
# -------------------------------
def normalize_plate(text):
    text = text.upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    text = text.replace('O', '0').replace('I', '1').replace('Z', '2')
    return text


# -------------------------------
# USER INDEX (CONNECT DRIVER)
# -------------------------------
def user_index(request):
    driver = None

    if request.method == "POST" and request.FILES.get("license"):
        plate_file = request.FILES["license"]

        # ✅ SAFE METHOD (WORKS ON RENDER)
        # Example: AP09AB1234.jpg → AP09AB1234
        plate_text = os.path.splitext(plate_file.name)[0]
        license_no = normalize_plate(plate_text)

        print("PLATE FROM FILE:", license_no)

        driver = UserModel.objects.filter(
            user_license__icontains=license_no,
            user_status="accepted"
        ).first()

        if not driver:
            messages.info(request, "No Driver Found With This Plate")
            return redirect("user_index")

    return render(request, "user/user-index.html", {"driver": driver})


# -------------------------------
# USER INTERACTIONS
# -------------------------------
def user_interactions(request):
    user_id = request.session.get("user_id")
    interactions = InteractionModel.objects.filter(from_user=user_id)
    paginator = Paginator(interactions, 5)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "user/user-interactions.html", {"a": page})


# -------------------------------
# USER PROFILE
# -------------------------------
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

        if request.FILES.get("photo"):
            user.user_photo = request.FILES["photo"]

        user.save()
        messages.success(request, "Profile updated successfully")
        return redirect("user_profile")

    return render(request, "user/user-profile.html", {"user": user})


# -------------------------------
# USER FEEDBACK
# -------------------------------
def user_feedback(request):
    user_id = request.session.get("user_id")
    user = UserModel.objects.get(user_id=user_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        review = request.POST.get("review")

        analyzer = SentimentIntensityAnalyzer()
        score = analyzer.polarity_scores(review)["compound"]

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


# -------------------------------
# CONTACT EMAIL / SMS
# -------------------------------
def contact_email(request, driver_id, text):
    user = UserModel.objects.get(user_id=request.session.get("user_id"))
    driver = UserModel.objects.get(user_id=driver_id)

    if request.method == "POST":
        message = request.POST.get("message")

        if text == "email":
            html = f"<p>From {user.user_name}</p><br>{message}"
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

    return render(request, "user/user-com.html", {"driver": driver, "text": text})


# -------------------------------
# CONTACT CALL
# -------------------------------
def contact_call(request, driver_id, text):
    user = UserModel.objects.get(user_id=request.session.get("user_id"))
    driver = UserModel.objects.get(user_id=driver_id)

    InteractionModel.objects.create(
        message="call",
        interac_type="call",
        to_user=driver,
        from_user=user,
    )

    messages.success(request, "Call registered")
    return redirect("user_index")
