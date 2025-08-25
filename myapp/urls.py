from django.urls import path
from . import views

app_name = 'myapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('control/', views.control, name='control'),
    path('tables/', views.tables, name='tables'),
    
    # API endpoints
    path('api/detection/start/', views.start_detection, name='start_detection'),
    path('api/detection/pause/', views.pause_detection, name='pause_detection'),
    path('api/detection/resume/', views.resume_detection, name='resume_detection'),
    path('api/detection/stop/', views.stop_detection, name='stop_detection'),
    path('api/video_feed/', views.video_feed, name='video_feed'),
    path('api/detection/get_counts/', views.get_counts, name='get_counts'),
    path('api/dashboard/week-data/', views.get_week_data, name='get_week_data'),
    path('api/dashboard/period-data/', views.get_period_data, name='get_period_data'),
    path('api/save_count_data/', views.save_count_data_api, name='save_count_data_api'),
    path('api/update_count_data/<int:record_id>/', views.update_count_data_api, name='update_count_data_api'),
] 