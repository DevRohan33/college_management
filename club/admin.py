from django.contrib import admin
from .models import (
    Club, ClubMember, ClubActivity, ClubEvent,
    ClubChat, ClubChatReaction, PollOption, PollVote
)

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "unique_id", "created_by", "created_at")
    search_fields = ("name", "unique_id", "description")
    list_filter = ("created_at",)


@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "club", "role", "status", "badge", "points", "joined_at")
    list_filter = ("role", "status", "badge")
    search_fields = ("user__username", "club__name")
    autocomplete_fields = ("user", "club")


@admin.register(ClubActivity)
class ClubActivityAdmin(admin.ModelAdmin):
    list_display = ("club", "created_by", "created_at")
    search_fields = ("content", "club__name", "created_by__username")
    list_filter = ("created_at",)


@admin.register(ClubEvent)
class ClubEventAdmin(admin.ModelAdmin):
    list_display = ("title", "club", "event_date", "created_by")
    search_fields = ("title", "description", "club__name")
    list_filter = ("event_date",)


@admin.register(ClubChat)
class ClubChatAdmin(admin.ModelAdmin):
    list_display = ("club", "sender", "created_at", "is_poll")
    search_fields = ("message", "sender__username", "club__name")
    list_filter = ("is_poll", "created_at")
    autocomplete_fields = ("club", "sender")


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ("chat", "option_text", "votes")
    search_fields = ("option_text", "chat__message")


@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ("user", "poll_option", "voted_at")
    search_fields = ("user__username", "poll_option__option_text")
    list_filter = ("voted_at",)


@admin.register(ClubChatReaction)
class ClubChatReactionAdmin(admin.ModelAdmin):
    list_display = ("chat", "user", "emoji", "created_at")
    search_fields = ("user__username", "emoji", "chat__message")
    list_filter = ("emoji", "created_at")
