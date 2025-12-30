import re

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import EmailMultiAlternatives

from car_social_network.settings import DEFAULT_FROM_EMAIL
from userapp.models import UserModel, InteractionModel, FeedbackModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# -----------------------
# Utility
# -----------------------
def normalize_plate(text):
    """
    Normalize license plate: remove special chars, convert to uppercase
    Example: TS-09-ET-7188 -> TS09ET7188
    """
    if not text:
        return ""
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


# -----------------------
# USER REGISTRATION
# -----------------------
def user_register(request):
    """Handle user registration with proper license plate normalization"""
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        password = request.POST.get("password")
        license = request.POST.get("license")
        # photo = request.FILES.get("photo")
        
        # Contact preferences
        contact1 = request.POST.get("contact1", "")
        contact2 = request.POST.get("contact2", "")
        contact3 = request.POST.get("contact3", "")
        


        # Privacy
        visibal = request.POST.get("visibal")
        
        # Validate required fields
      
        if not name or not email or not contact or not password or not license or not visibal:
            messages.error(request, "All fields are required")
            return redirect("user_register")

# At least one contact method must be selected
        if not (contact1 or contact2 or contact3):
            messages.error(request, "Select at least one contact method")
            return redirect("user_register")
        
        # Normalize license plate
        normalized_license = normalize_plate(license)
        
        # Check if email already exists
        if UserModel.objects.filter(user_email=email).exists():
            messages.warning(request, "Email already registered")
            return redirect("user_register")
        
        # Check if license plate already exists
        if UserModel.objects.filter(user_license=normalized_license).exists():
            messages.warning(request, "License plate already registered")
            return redirect("user_register")
        
        try:
            # Create user
            user = UserModel.objects.create(
                user_name=name,
                user_email=email,
                user_contact=contact,
                user_password=password,
                user_license=normalized_license,
                user_photo=photo,
                user_email_status=contact1 if contact1 else "",
                user_sms_status=contact2 if contact2 else "",
                user_call_status=contact3 if contact3 else "",
                user_privacy_status=visibal,
                user_status="pending"  # Admin approval needed
            )
            
            messages.success(request, "Registration successful! Please wait for admin approval.")
            return redirect("home_user_login")
            
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect("user_register")
    
    return render(request, "home/user-register.html")


# -----------------------
# USER INDEX (CONNECT)
# -----------------------
def user_index(request):
    """Search for driver by license plate"""
    if request.method == "POST":
        plate_text = request.POST.get("plate_text")

        if not plate_text:
            messages.error(request, "Please enter license plate number")
            return redirect("user_index")

        # Normalize the search input
        plate = normalize_plate(plate_text)
        
        # Debug logging (optional - remove in production)
        print(f"SEARCH INPUT: {plate_text}")
        print(f"NORMALIZED SEARCH: {plate}")

        # Search for driver with exact match (case insensitive)
        driver = UserModel.objects.filter(
            user_license=plate,  # Exact match since both are normalized
            user_status="accepted"
        ).first()

        if not driver:
            messages.info(request, f"No Driver Found With License Plate: {plate_text}")
            return redirect("user_index")

        return render(request, "user/user-index.html", {"driver": driver})

    return render(request, "user/user-index.html")


# -----------------------
# USER INTERACTIONS
# -----------------------
def user_interactions(request):
    """View user's interaction history"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("home_user_login")
    
    interactions = InteractionModel.objects.filter(
        from_user_id=user_id
    ).order_by('-interac_id')

    paginator = Paginator(interactions, 5)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "user/user-interactions.html", {"a": page})


# -----------------------
# USER PROFILE
# -----------------------
def user_profile(request):
    """View and edit user profile"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("home_user_login")
    
    try:
        user = UserModel.objects.get(user_id=user_id)
    except UserModel.DoesNotExist:
        messages.error(request, "User not found")
        return redirect("home_user_login")

    if request.method == "POST":
        user.user_name = request.POST.get("name")
        user.user_email = request.POST.get("email")
        user.user_password = request.POST.get("password")
        user.user_contact = request.POST.get("contact")
        user.user_privacy_status = request.POST.get("privacy")
        
        # Normalize license plate on update
        license = request.POST.get("license")
        if license:
            normalized_license = normalize_plate(license)
            
            # Check if new license already exists (excluding current user)
            existing = UserModel.objects.filter(
                user_license=normalized_license
            ).exclude(user_id=user_id).exists()
            
            if existing:
                messages.warning(request, "License plate already registered by another user")
                return redirect("user_profile")
            
            user.user_license = normalized_license

        if request.FILES.get("photo"):
            user.user_photo = request.FILES["photo"]

        user.save()
        messages.success(request, "Profile updated successfully")
        return redirect("user_profile")

    return render(request, "user/user-profile.html", {"user": user})


# -----------------------
# USER FEEDBACK
# -----------------------
def user_feedback(request):
    """Submit feedback with sentiment analysis"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("home_user_login")
    
    try:
        user = UserModel.objects.get(user_id=user_id)
    except UserModel.DoesNotExist:
        messages.error(request, "User not found")
        return redirect("home_user_login")

    if request.method == "POST":
        rating = request.POST.get("rating")
        review = request.POST.get("review")
        
        if not rating or not review:
            messages.error(request, "Please provide both rating and review")
            return redirect("user_feedback")

        try:
            # Sentiment analysis
            analyzer = SentimentIntensityAnalyzer()
            score = analyzer.polarity_scores(review)["compound"]

            sentiment = "neutral"
            if score > 0.05:
                sentiment = "positive"
            elif score < -0.05:
                sentiment = "negative"

            FeedbackModel.objects.create(
                reviewer=user,
                rating=rating,
                review=review,
                sentiment=sentiment,
            )

            messages.success(request, "Feedback submitted successfully")
            return redirect("user_feedback")
            
        except Exception as e:
            messages.error(request, f"Failed to submit feedback: {str(e)}")
            return redirect("user_feedback")

    return render(request, "user/user-feedback.html")


# -----------------------
# CONTACT EMAIL/SMS
# -----------------------
def contact_email(request, driver_id, text):
    """Handle email and SMS communication"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("home_user_login")
    
    try:
        user = UserModel.objects.get(user_id=user_id)
        driver = UserModel.objects.get(user_id=driver_id)
    except UserModel.DoesNotExist:
        messages.error(request, "User not found")
        return redirect("user_index")

    if request.method == "POST":
        message = request.POST.get("message")
        
        if not message:
            messages.error(request, "Please enter a message")
            return render(request, "user/user-com.html", {"driver": driver, "text": text})

        try:
            if text == "email":
                # Send email
                html = f"""
                <h3>Message from Car Social Network</h3>
                <p><strong>From:</strong> {user.user_name}</p>
                <p><strong>Email:</strong> {user.user_email}</p>
                <p><strong>Contact:</strong> {user.user_contact}</p>
                <hr>
                <p>{message}</p>
                """
                
                msg = EmailMultiAlternatives(
                    "Car Social Network - New Message",
                    html,
                    DEFAULT_FROM_EMAIL,
                    [driver.user_email],
                )
                msg.attach_alternative(html, "text/html")
                msg.send()
                
                messages.success(request, "Email sent successfully")
                
            elif text == "sms":
                # Log SMS (actual SMS sending would require SMS gateway integration)
                messages.success(request, "SMS request logged successfully")

            # Record interaction
            InteractionModel.objects.create(
                message=message,
                interac_type=text,
                to_user=driver,
                from_user=user,
            )
            
            return redirect("user_interactions")
            
        except Exception as e:
            messages.error(request, f"Failed to send message: {str(e)}")

    return render(request, "user/user-com.html", {"driver": driver, "text": text})


# -----------------------
# CONTACT CALL
# -----------------------
def contact_call(request, driver_id, text):
    """Handle call request"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("home_user_login")
    
    try:
        user = UserModel.objects.get(user_id=user_id)
        driver = UserModel.objects.get(user_id=driver_id)
    except UserModel.DoesNotExist:
        messages.error(request, "User not found")
        return redirect("user_index")

    try:
        # Record call interaction
        InteractionModel.objects.create(
            message=f"Call request to {driver.user_name}",
            interac_type="call",
            to_user=driver,
            from_user=user,
        )

        messages.success(request, f"Call: {driver.user_contact}")
        
    except Exception as e:
        messages.error(request, f"Failed to log call: {str(e)}")
    
    return redirect("user_index")