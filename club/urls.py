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

    # Firebase chat integration
    path("<str:unique_id>/chat/config/", views.firebase_config, name="firebase_config"),
    path("<str:unique_id>/chat/send/", views.send_message, name="send_message"),
    path("<str:unique_id>/chat/poll/", views.send_poll, name="send_poll"),
    path("<str:unique_id>/chat/poll/vote/", views.vote_poll, name="vote_poll"),
    path("<str:unique_id>/chat/react/", views.toggle_reaction, name="react_message"),
    path("<str:unique_id>/chat/typing/", views.typing_status, name="typing_status"),
    path("<str:unique_id>/chat/online/", views.online_members, name="online_members"),

    # Club activities & events
    path("<str:unique_id>/activities/", views.club_activities, name="club_activities"),
    path("<str:unique_id>/events/", views.club_events, name="club_events"),
]
