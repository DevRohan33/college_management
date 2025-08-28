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
from .models import Club, ClubMember,  ClubActivity, ClubEvent , EventRSVP , ActivityLike, ActivityComment
from django.utils.text import slugify
from django import forms
import json
from django.core.cache import cache
from django.utils.timezone import now
from django.conf import settings
from .firebase_config import db
from account.models import User
from django.views.decorators.http import require_POST

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
        .select_related('created_by')
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
# @login_required
# def firebase_config(request, unique_id):
#     """Return Firebase config for frontend"""
#     club = get_object_or_404(Club, unique_id=unique_id)
#     membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
#     if not membership:
#         return JsonResponse({"error": "Not authorized"}, status=403)

#     # Normally load from settings.py
#     config = {
#         "apiKey": settings.FIREBASE_API_KEY,
#         "authDomain": settings.FIREBASE_AUTH_DOMAIN,
#         "databaseURL": settings.FIREBASE_DB_URL,
#         "projectId": settings.FIREBASE_PROJECT_ID,
#         "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
#         "messagingSenderId": settings.FIREBASE_MSG_SENDER_ID,
#         "appId": settings.FIREBASE_APP_ID,
#     }
#     return JsonResponse(config)

@login_required
def firebase_config(request, unique_id):
    """Return Firebase config for frontend"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(
        club=club, user=request.user, status="active"
    ).first()
    if not membership:
        return JsonResponse({"error": "Not authorized"}, status=403)

    return JsonResponse(settings.FIREBASE_FRONTEND)


@login_required
def club_chat(request, unique_id):
    """Render the chat page for a specific club"""
    club = get_object_or_404(Club, unique_id=unique_id)

    # Ensure user is an active member
    membership = ClubMember.objects.filter(
        club=club, user=request.user, status="active"
    ).first()
    if not membership:
        messages.error(request, "🚫 You must be a member to access the chat.")
        return redirect("club:club_detail", unique_id=unique_id)

    return render(request, "club/chat.html", {
        "club": club,
        "membership": membership,
        "firebase_chat_enabled": True,
        "FIREBASE_FRONTEND": json.dumps(settings.FIREBASE_FRONTEND),
    })

# -------------------- Club Chat ------------------
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
        from django.core.files.storage import default_storage
        path = default_storage.save(f"chat_media/{media_file.name}", media_file)
        media_url = default_storage.url(path)

    sender_name = request.user.first_name or request.user.username

    message_data = {
        "sender": sender_name,
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

    sender_name = request.user.first_name or request.user.username

    poll_data = {
        "sender": sender_name,
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

    sender_name = request.user.first_name or request.user.username

    ref = db.reference(f"clubs/{unique_id}/messages/{message_id}/options/{option_index}/votes")
    ref.update({sender_name: True})  # mark user voted

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

    sender_name = request.user.first_name or request.user.username

    ref = db.reference(f"clubs/{unique_id}/messages/{message_id}/reactions/{emoji}")
    reactions = ref.get() or {}

    if sender_name in reactions:
        del reactions[sender_name]
    else:
        reactions[sender_name] = True

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

    sender_name = request.user.first_name or request.user.username

    from .firebase_config import db
    ref = db.reference(f"clubs/{unique_id}/typing/{sender_name}")
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

#-------------------- Club Activities ------------------

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
def like_activity(request, activity_id):
    activity = get_object_or_404(ClubActivity, id=activity_id)

    like, created = ActivityLike.objects.get_or_create(user=request.user, activity=activity)

    if not created:
        # already liked → unlike
        like.delete()
        messages.info(request, "👍 Like removed")
    else:
        messages.success(request, "❤️ You liked this activity")

    return redirect("club:club_activities", unique_id=activity.club.unique_id)

@login_required
def comment_activity(request, activity_id):
    activity = get_object_or_404(ClubActivity, id=activity_id)

    if request.method == "POST":
        comment_text = request.POST.get("comment", "").strip()
        if comment_text.strip():
            ActivityComment.objects.create(
                user=request.user,
                activity=activity,
                content=comment_text
            )
            messages.success(request, "💬 Comment added")

    return redirect("club:club_activities", unique_id=activity.club.unique_id)

@login_required
def delete_activity(request, activity_id):
    activity = get_object_or_404(ClubActivity, id=activity_id)

    membership = ClubMember.objects.filter(club=activity.club, user=request.user, status="active").first()
    if not membership or membership.role not in ["owner", "admin", "moderator"]:
        messages.error(request, "🚫 You don’t have permission to delete this activity.")
        return redirect("club:club_activities", unique_id=activity.club.unique_id)

    activity.delete()
    messages.success(request, "🗑️ Activity deleted")
    return redirect("club:club_activities", unique_id=activity.club.unique_id)

#-------------------- Club Events ------------------
@login_required
@require_POST
def rsvp_event(request, club_unique_id, event_id):
    """Handle RSVP responses for events"""
    try:
        club = get_object_or_404(Club, unique_id=club_unique_id)
        event = get_object_or_404(ClubEvent, id=event_id, club=club)
        
        # Check if user is a member of the club
        if not ClubMember.objects.filter(club=club, user=request.user).exists():
            return JsonResponse({'success': False, 'error': 'You must be a club member to RSVP'})
        
        data = json.loads(request.body)
        response = data.get('response')
        
        if response not in ['yes', 'maybe', 'no']:
            return JsonResponse({'success': False, 'error': 'Invalid RSVP response'})
        
        # Update or create RSVP
        rsvp, created = EventRSVP.objects.update_or_create(
            user=request.user,
            event=event,
            defaults={'response': response}
        )
        
        # Get updated counts
        counts = {
            'yes': EventRSVP.objects.filter(event=event, response='yes').count(),
            'maybe': EventRSVP.objects.filter(event=event, response='maybe').count(),
            'no': EventRSVP.objects.filter(event=event, response='no').count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': f'RSVP updated to {response}',
            'counts': counts,
            'user_response': response
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def edit_event(request, club_unique_id, event_id):
    """Edit an existing event"""
    try:
        club = get_object_or_404(Club, unique_id=club_unique_id)
        event = get_object_or_404(ClubEvent, id=event_id, club=club)

        # Check membership
        membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
        if not (membership and membership.role in ["owner", "admin"] and event.created_by == request.user):
            return JsonResponse({'success': False, 'error': 'Permission denied'})

        data = json.loads(request.body)

        if 'title' in data and data['title'].strip():
            event.title = data['title'].strip()

        if 'description' in data:
            event.description = data['description']

        if 'event_date' in data:
            from datetime import datetime
            try:
                event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
                if event_date > timezone.now():
                    event.event_date = event_date
                else:
                    return JsonResponse({'success': False, 'error': 'Event date must be in the future'})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date format'})

        event.save()

        return JsonResponse({
            'success': True,
            'message': 'Event updated successfully',
            'event': {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'event_date': event.event_date.isoformat(),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def delete_event(request, club_unique_id, event_id):
    """Delete an event"""
    try:
        club = get_object_or_404(Club, unique_id=club_unique_id)
        event = get_object_or_404(ClubEvent, id=event_id, club=club)

        membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
        if not (membership and membership.role in ["owner", "admin"] and event.created_by == request.user):
            return JsonResponse({'success': False, 'error': 'Permission denied'})

        event_title = event.title
        event.delete()

        return JsonResponse({
            'success': True,
            'message': f'Event \"{event_title}\" deleted successfully'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_event_rsvps(request, club_unique_id, event_id):
    """Get RSVP counts and user's response for an event"""
    try:
        club = get_object_or_404(Club, unique_id=club_unique_id)
        event = get_object_or_404(ClubEvent, id=event_id, club=club)
        
        counts = {
            'yes': EventRSVP.objects.filter(event=event, response='yes').count(),
            'maybe': EventRSVP.objects.filter(event=event, response='maybe').count(),
            'no': EventRSVP.objects.filter(event=event, response='no').count(),
        }
        
        user_rsvp = None
        if request.user.is_authenticated:
            try:
                rsvp = EventRSVP.objects.get(event=event, user=request.user)
                user_rsvp = rsvp.response
            except EventRSVP.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'counts': counts,
            'user_response': user_rsvp
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Update your existing club_events view to include RSVP data
@login_required
def club_events(request, unique_id):
    club = get_object_or_404(Club, unique_id=unique_id)

    # Check membership
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        messages.error(request, "You must be a club member to view events.")
        return redirect('club:club_detail', unique_id=unique_id)

    is_admin = membership.role in ["owner", "admin"]

    now = timezone.now()
    upcoming_events = ClubEvent.objects.filter(club=club, event_date__gt=now).order_by('event_date')
    past_events = ClubEvent.objects.filter(club=club, event_date__lte=now).order_by('-event_date')[:5]

    for event in upcoming_events:
        event.rsvp_counts = {
            'yes': EventRSVP.objects.filter(event=event, response='yes').count(),
            'maybe': EventRSVP.objects.filter(event=event, response='maybe').count(),
            'no': EventRSVP.objects.filter(event=event, response='no').count(),
        }
        try:
            user_rsvp = EventRSVP.objects.get(event=event, user=request.user)
            event.user_rsvp = user_rsvp.response
        except EventRSVP.DoesNotExist:
            event.user_rsvp = None

    form = None
    if is_admin and request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.club = club
            event.created_by = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('club:club_events', unique_id=unique_id)
    elif is_admin:
        form = EventForm()

    context = {
        'club': club,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'is_admin': is_admin,
        'form': form,
        'current_user': request.user,
    }

    return render(request, 'club/events.html', context)


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