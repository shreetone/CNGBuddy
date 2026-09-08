from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    #PUBLIC URLs
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contact_view, name='contacts'),
    path('contact/', views.contact_view, name='contact'),  # alias
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('map/', views.map_view, name='map'),
    path('pump/<str:pump_id>/', views.pump_detail, name='pump_detail'),

    #AUTH
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register_user, name='register'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('login-redirect/', views.login_redirect, name='login_redirect'),

    #USER
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('support/', views.support_ticket, name='support'),
    path('feedback/', views.submit_feedback, name='feedback'),

    #ADMIN SUPPORT / CONTACT
    path('panel/support/', views.admin_support, name='admin_support'),
    path('admin/contacts/', views.admin_contacts, name='admin_contacts'),
    path('admin/support/delete/<str:ticket_id>/', views.delete_ticket, name='delete_ticket'),

    #ADMIN FEEDBACK
    path('panel/feedback/', views.admin_feedbacks, name='admin_feedback'),
    path('panel/feedbacks/approve/<str:feedback_id>/', views.approve_feedback, name='approve_feedback'),
    path('panel/feedbacks/delete/<str:feedback_id>/', views.delete_feedback, name='delete_feedback'),
    path("feedback/", views.submit_feedback, name="submit_feedback"),

    #BOOKINGS
    path('book/<str:pump_id>/', views.book_pump, name='book_pump'),
    path('cancel/<str:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('invoice/<str:booking_id>/', views.invoice, name='invoice'),
    path('booking/reschedule/<str:booking_id>/', views.reschedule_booking, name='reschedule_booking'),
    path('payment/<str:booking_id>/', views.payment, name='payment'),

    #ADMIN PUMPS
    path('admin/pumps/', views.admin_pumps, name='admin_pumps'),
    path('admin/pumps/add/', views.admin_add_pump, name='admin_add_pump'),
    path('admin/pumps/edit/<str:pump_id>/', views.admin_edit_pump, name='admin_edit_pump'),
    path('admin/pumps/delete/<str:pump_id>/', views.admin_delete_pump, name='admin_delete_pump'),
    path('admin/pumps/toggle/<str:pump_id>/', views.toggle_pump, name='toggle_pump'),
    path('admin/bookings/', views.admin_bookings, name='admin_bookings'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),

    #RATINGS 
    path('pump/<str:pump_id>/rate/', views.rate_pump, name='rate_pump'),

    #API
    path('api/queue/<str:pump_id>/', views.pump_queue, name='pump_queue'),
    path('api/nearest-pumps/', views.nearest_pumps, name='nearest_pumps'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),

    #UTILITY
    path('test-reminder/', views.test_reminder, name='test_reminder'),
]
