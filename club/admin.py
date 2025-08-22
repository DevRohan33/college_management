from django.contrib import admin
from .models import Club, ClubMember, ClubChat, ClubActivity, ClubEvent


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "unique_id", "created_by", "created_at")
    search_fields = ("name", "unique_id", "created_by__username")
    readonly_fields = ("unique_id", "created_at")


@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ("club", "user", "role", "status", "badge", "points", "joined_at")
    list_filter = ("role", "status", "badge")
    search_fields = ("club__name", "user__username")
    ordering = ("-joined_at",)


@admin.register(ClubChat)
class ClubChatAdmin(admin.ModelAdmin):
    list_display = ("club", "sender", "message", "created_at")
    search_fields = ("message", "sender__username")
    ordering = ("-created_at",)


@admin.register(ClubActivity)
class ClubActivityAdmin(admin.ModelAdmin):
    list_display = ("club", "created_by", "content", "created_at")
    search_fields = ("content", "created_by__username")
    ordering = ("-created_at",)


@admin.register(ClubEvent)
class ClubEventAdmin(admin.ModelAdmin):
    list_display = ("club", "title", "event_date", "created_by", "created_at")
    search_fields = ("title", "description")
    ordering = ("event_date",)
