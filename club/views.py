from django.views.decorators.http import require_http_methods
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Club, ClubMember,  ClubActivity, ClubEvent
from django.utils.text import slugify
from django import forms
import json
from django.core.cache import cache
from django.utils.timezone import now
from django.conf import settings
from .firebase_config import db

# ------------------ FORMS ------------------
class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["name", "description"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter club name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your club...'})
        }


class ActivityForm(forms.ModelForm):
    class Meta:
        model = ClubActivity
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Share an announcement or update...'
            })
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = ClubEvent
        fields = ['title', 'description', 'event_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'event_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
        }


# ------------------ VIEWS ------------------
@login_required
def club_list(request):
    """Show all clubs with search and pagination"""
    query = request.GET.get("q", "")
    clubs = (
        Club.objects.annotate(member_count=Count('memberships'))
        .select_related('owner')
        .prefetch_related('memberships')
        .order_by('-created_at')
    )

    if query:
        clubs = clubs.filter(
            Q(name__icontains=query) |
            Q(unique_id__icontains=query) |
            Q(description__icontains=query)
        )

    paginator = Paginator(clubs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    user_clubs = Club.objects.filter(
        memberships__user=request.user,
        memberships__status='active'
    )

    return render(request, "club/club_list.html", {
        "clubs": page_obj,
        "query": query,
        "user_clubs": user_clubs,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
    })

@login_required
def club_detail(request, unique_id):
    """Enhanced club detail with activities and Firebase-powered chat"""
    club = get_object_or_404(Club, unique_id=unique_id)
    
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    is_admin = membership and membership.role in ["owner", "admin"]
    is_member = membership is not None

    # Get recent activities and events
    recent_activities = ClubActivity.objects.filter(club=club).order_by("-created_at")[:5]
    upcoming_events = ClubEvent.objects.filter(club=club, event_date__gte=timezone.now()).order_by("event_date")[:3]

    # NOTE: Chats are handled by Firebase Realtime DB, not Django
    # So we just pass the club ID and let frontend fetch from Firebase

    member_stats = {
        "total_members": ClubMember.objects.filter(club=club, status="active").count(),
        "pending_requests": ClubMember.objects.filter(club=club, status="pending").count() if is_admin else 0,
    }

    return render(request, "club/club_detail.html", {
        "club": club,
        "membership": membership,
        "is_admin": is_admin,
        "is_member": is_member,
        "recent_activities": recent_activities,
        "upcoming_events": upcoming_events,
        "member_stats": member_stats,
        "firebase_chat_enabled": True,   # <-- flag for frontend
    })


@login_required
def create_club(request):
    """Create a new club with enhanced form"""
    if request.method == "POST":
        form = ClubForm(request.POST)
        if form.is_valid():
            club = form.save(commit=False)
            club.created_by = request.user
            club.save()

            # Add creator as owner
            ClubMember.objects.create(
                club=club,
                user=request.user,
                role="owner",
                status="active"
            )

            messages.success(request, f"🎉 Club '{club.name}' created successfully!")
            return redirect("club:club_detail", unique_id=club.unique_id)
    else:
        form = ClubForm()

    return render(request, "club/create_club.html", {"form": form})


@login_required
def send_join_request(request, unique_id):
    """User sends request to join club"""
    club = get_object_or_404(Club, unique_id=unique_id)

    membership, created = ClubMember.objects.get_or_create(club=club, user=request.user)

    if not created:
        if membership.status == "pending":
            messages.info(request, "⏳ You have already requested to join this club.")
        elif membership.status == "active":
            messages.success(request, "✅ You are already a member of this club.")
        elif membership.status == "banned":
            messages.error(request, "🚫 You are banned from this club.")
    else:
        membership.status = "pending"
        membership.save()
        messages.success(request, "📤 Your join request has been sent!")

    return redirect("club:club_detail", unique_id=unique_id)


@login_required
def manage_members(request, unique_id):
    """Enhanced member management"""
    club = get_object_or_404(Club, unique_id=unique_id)

    membership = ClubMember.objects.filter(
        club=club, user=request.user, status="active"
    ).first()

    if not membership or membership.role not in ["owner", "admin"]:
        messages.error(request, "🚫 You don't have permission to manage this club.")
        return redirect("club:club_detail", unique_id=unique_id)

    pending_requests = ClubMember.objects.filter(club=club, status="pending").order_by('-joined_at')
    active_members = ClubMember.objects.filter(club=club, status="active").order_by('-joined_at')

    return render(request, "club/manage_members.html", {
        "club": club,
        "pending_requests": pending_requests,
        "active_members": active_members,
        "user_role": membership.role
    })


#-------------------- Club Chat ------------------
@login_required
def firebase_config(request, unique_id):
    """Return Firebase config for frontend"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({"error": "Not authorized"}, status=403)

    # Normally load from settings.py
    config = {
        "apiKey": settings.FIREBASE_API_KEY,
        "authDomain": settings.FIREBASE_AUTH_DOMAIN,
        "databaseURL": settings.FIREBASE_DB_URL,
        "projectId": settings.FIREBASE_PROJECT_ID,
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": settings.FIREBASE_MSG_SENDER_ID,
        "appId": settings.FIREBASE_APP_ID,
    }
    return JsonResponse(config)

@login_required
@require_http_methods(["POST"])
def send_message(request, unique_id):
    """Send chat message directly to Firebase"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({"error": "Not authorized"}, status=403)

    message_text = request.POST.get("message", "").strip()
    media_file = request.FILES.get("media")

    media_url = None
    if media_file:
        # save file to Django media folder (or cloud)
        from django.core.files.storage import default_storage
        path = default_storage.save(f"chat_media/{media_file.name}", media_file)
        media_url = default_storage.url(path)

    message_data = {
        "sender": request.user.username,
        "message": message_text if message_text else (media_file.name if media_file else ""),
        "media_url": media_url,
        "created_at": timezone.now().isoformat()
    }

    ref = db.reference(f"clubs/{unique_id}/messages")
    ref.push(message_data)

    return JsonResponse({"success": True, "message": message_data})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_poll(request, unique_id):
    """Send a poll in chat"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({"error": "Not authorized"}, status=403)

    data = json.loads(request.body)
    question = data.get("question", "").strip()
    options = data.get("options", [])

    if not question or len(options) < 2:
        return JsonResponse({"error": "Poll must have at least 2 options"}, status=400)

    poll_data = {
        "sender": request.user.username,
        "type": "poll",
        "question": question,
        "options": {i: {"text": opt, "votes": {}} for i, opt in enumerate(options)},
        "created_at": timezone.now().isoformat()
    }

    ref = db.reference(f"clubs/{unique_id}/messages")
    ref.push(poll_data)

    return JsonResponse({"success": True})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def vote_poll(request, unique_id):
    """Vote in a poll"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({"error": "Not authorized"}, status=403)

    data = json.loads(request.body)
    message_id = data.get("message_id")
    option_index = str(data.get("option_index"))

    ref = db.reference(f"clubs/{unique_id}/messages/{message_id}/options/{option_index}/votes")
    ref.update({request.user.username: True})  # mark user voted

    return JsonResponse({"success": True})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def toggle_reaction(request, unique_id):
    """Add/remove emoji reaction (Firebase only)"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({"error": "Not authorized"}, status=403)

    data = json.loads(request.body)
    message_id = data.get("message_id")
    emoji = data.get("emoji")

    ref = db.reference(f"clubs/{unique_id}/messages/{message_id}/reactions/{emoji}")
    reactions = ref.get() or {}

    if request.user.username in reactions:
        # remove reaction
        del reactions[request.user.username]
    else:
        # add reaction
        reactions[request.user.username] = True

    ref.set(reactions)
    return JsonResponse({"success": True, "emoji": emoji, "count": len(reactions)})
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def typing_status(request, unique_id):
    """User typing indicator"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({"error": "Not authorized"}, status=403)

    data = json.loads(request.body)
    is_typing = data.get("is_typing", False)

    from .firebase_config import db
    ref = db.reference(f"clubs/{unique_id}/typing/{request.user.username}")
    if is_typing:
        ref.set({"typing": True, "timestamp": timezone.now().isoformat()})
    else:
        ref.delete()

    return JsonResponse({"success": True})

@login_required
def online_members(request, unique_id):
    """Return list of online members (from cache or Firebase)"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({"error": "Not authorized"}, status=403)

    from .firebase_config import db
    ref = db.reference(f"clubs/{unique_id}/presence")
    snapshot = ref.get() or {}

    members_data = [
        {"username": user, "online": data.get("online", True)}
        for user, data in snapshot.items()
    ]

    return JsonResponse({"count": len(members_data), "members": members_data})

#-------------------- Club Activities & Events ------------------

@login_required
def club_activities(request, unique_id):
    """Club activities/feed page"""
    club = get_object_or_404(Club, unique_id=unique_id)
    
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        messages.error(request, "🚫 You must be a member to view activities.")
        return redirect("club:club_detail", unique_id=unique_id)

    activities = ClubActivity.objects.filter(club=club).order_by('-created_at')
    
    activity_form = ActivityForm()
    is_admin = membership.role in ["owner", "admin", "moderator"]

    if request.method == 'POST' and is_admin:
        activity_form = ActivityForm(request.POST)
        if activity_form.is_valid():
            activity = activity_form.save(commit=False)
            activity.club = club
            activity.created_by = request.user
            activity.save()
            messages.success(request, "📢 Activity posted!")
            return redirect("club:club_activities", unique_id=unique_id)

    return render(request, "club/activities.html", {
        "club": club,
        "activities": activities,
        "form": activity_form,
        "is_admin": is_admin,
        "membership": membership
    })

@login_required
def club_events(request, unique_id):
    """Club events page"""
    club = get_object_or_404(Club, unique_id=unique_id)
    
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        messages.error(request, "🚫 You must be a member to view events.")
        return redirect("club:club_detail", unique_id=unique_id)

    upcoming_events = ClubEvent.objects.filter(club=club, event_date__gte=timezone.now()).order_by('event_date')
    past_events = ClubEvent.objects.filter(club=club, event_date__lt=timezone.now()).order_by('-event_date')[:10]
    
    event_form = EventForm()
    is_admin = membership.role in ["owner", "admin", "moderator"]

    if request.method == 'POST' and is_admin:
        event_form = EventForm(request.POST)
        if event_form.is_valid():
            event = event_form.save(commit=False)
            event.club = club
            event.created_by = request.user
            event.save()
            messages.success(request, "📅 Event created!")
            return redirect("club:club_events", unique_id=unique_id)

    return render(request, "club/events.html", {
        "club": club,
        "upcoming_events": upcoming_events,
        "past_events": past_events,
        "form": event_form,
        "is_admin": is_admin,
        "membership": membership
    })

@login_required
def approve_request(request, unique_id, member_id):
    """Approve a pending join request"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = get_object_or_404(ClubMember, id=member_id, club=club, status="pending")

    admin_member = ClubMember.objects.filter(club=club, user=request.user, role__in=["owner", "admin"]).first()
    if not admin_member:
        messages.error(request, "🚫 Permission denied.")
        return redirect("club:club_detail", unique_id=unique_id)

    membership.status = "active"
    membership.save()
    messages.success(request, f"✅ {membership.user.username} has been approved!")
    return redirect("club:manage_members", unique_id=unique_id)

@login_required
def reject_request(request, unique_id, member_id):
    """Reject a pending request"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = get_object_or_404(ClubMember, id=member_id, club=club, status="pending")

    admin_member = ClubMember.objects.filter(club=club, user=request.user, role__in=["owner", "admin"]).first()
    if not admin_member:
        messages.error(request, "🚫 Permission denied.")
        return redirect("club:club_detail", unique_id=unique_id)

    membership.delete()
    messages.info(request, f"❌ Join request from {membership.user.username} rejected.")
    return redirect("club:manage_members", unique_id=unique_id)


@login_required
def remove_member(request, unique_id, member_id):
    """Remove a member from the club"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = get_object_or_404(ClubMember, id=member_id, club=club, status="active")

    admin_member = ClubMember.objects.filter(club=club, user=request.user, role__in=["owner", "admin"]).first()
    if not admin_member:
        messages.error(request, "🚫 Permission denied.")
        return redirect("club:club_detail", unique_id=unique_id)

    membership.delete()
    messages.warning(request, f"🚮 {membership.user.username} has been removed from the club.")
    return redirect("club:manage_members", unique_id=unique_id)