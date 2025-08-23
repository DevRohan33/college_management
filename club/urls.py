from django.urls import path
from . import views

app_name = "club"

urlpatterns = [
    # Main club pages
    path("", views.club_list, name="club_list"),
    path("create/", views.create_club, name="create_club"),
    path("<str:unique_id>/", views.club_detail, name="club_detail"),
    
    # Membership management
    path("<str:unique_id>/join/", views.send_join_request, name="send_join_request"),
    path("<str:unique_id>/manage/", views.manage_members, name="manage_members"),
    path("<str:unique_id>/approve/<int:member_id>/", views.approve_request, name="approve_request"),
    path("<str:unique_id>/reject/<int:member_id>/", views.reject_request, name="reject_request"),
    path("<str:unique_id>/remove/<int:member_id>/", views.remove_member, name="remove_member"),
    
    # Club features
    path('<str:unique_id>/chat/', views.club_chat, name='club_chat'),
    # path('<str:unique_id>/chat/send/', views.send_chat_message, name='send_chat_message'),
    # path('<str:unique_id>/chat/typing/', views.typing_indicator, name='typing_indicator'),
    path('<str:unique_id>/chat/poll/create/', views.create_poll, name='create_poll'),
    path('<str:unique_id>/chat/poll/vote/', views.vote_poll, name='vote_poll'),
    path('<str:unique_id>/chat/online/', views.online_members, name='online_members'),
    # path('<str:unique_id>/chat/messages/', views.get_new_messages, name='get_new_messages'),
    path("<str:unique_id>/chat/react/", views.toggle_reaction, name="react_message"),


    path("<str:unique_id>/activities/", views.club_activities, name="club_activities"),
    path("<str:unique_id>/events/", views.club_events, name="club_events"),
]