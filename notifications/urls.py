from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('read/<int:notification_id>/', views.mark_notification_read, name='read'),
    path('read-all/', views.mark_all_notifications_read, name='read_all'),
    path('unread-count/', views.unread_notifications_count, name='unread_count'),
]
