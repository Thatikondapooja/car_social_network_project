from django.contrib import admin
from django.urls import path
from adminapp import views as adminapp_views
from mainapp import views as mainapp_views
from userapp import views as userapp_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # Admin panel
    path('admin/', admin.site.urls),

    # Admin app URLs
    path('admin-index', adminapp_views.admin_index, name='admin_index'),
    path('admin-pending-users', adminapp_views.admin_pending_users, name='admin_pending_users'),
    path('admin-all-users', adminapp_views.admin_all_users, name='admin_all_users'),
    path('admin-interactions', adminapp_views.admin_interactions, name='admin_interactions'),
    path('admin-user-feedback', adminapp_views.admin_user_feedback, name='admin_user_feedback'),
    path('admin-sentiment-analysis', adminapp_views.admin_sentiment_analysis, name='admin_sentiment_analysis'),
    path('admin-accept-user/<int:user_id>', adminapp_views.accept_user, name='accept_user'),
    path('admin-decline-user/<int:user_id>', adminapp_views.decline_user, name='decline_user'),

    # Home app URLs
    path('', mainapp_views.home_index, name='home_index'),
    path('home-admin-login', mainapp_views.home_admin_login, name='home_admin_login'),
    path('home-user-login', mainapp_views.home_user_login, name='home_user_login'),
    path('home-user-reg', mainapp_views.home_user_reg, name='home_user_reg'),
    path('about', mainapp_views.about, name='about'),

    # User app URLs
    path('user-index', userapp_views.user_index, name='user_index'),
    path('user-interactions', userapp_views.user_interactions, name='user_interactions'),
    path('user-profile', userapp_views.user_profile, name='user_profile'),
    path('user-feedback', userapp_views.user_feedback, name='user_feedback'),
    path('contact-email/<int:driver_id>/<str:text>', userapp_views.contact_email, name='contact_email'),
    path('contact_call/<int:driver_id>/<str:text>', userapp_views.contact_call, name='contact_call'),

]

# Media files (development / render)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
