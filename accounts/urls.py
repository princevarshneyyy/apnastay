from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('become-host/', views.become_host_view, name='become_host'),
    path('dashboard/guest/', views.guest_dashboard_view, name='guest_dashboard'),
    path('dashboard/host/', views.host_dashboard_view, name='host_dashboard'),
]
