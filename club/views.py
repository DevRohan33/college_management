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
from .models import Club, ClubMember, ClubChat, ClubActivity, ClubEvent, PollOption, PollVote
from django.utils.text import slugify
from django import forms
import json
from django.core.cache import cache
from django.utils.timezone import now

# ------------------ FORMS ------------------
class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["name", "description"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter club name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your club...'})
        }


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ClubChat
        fields = ['message']
        widgets = {
            'message': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Type your message...',
                'id': 'chat-input'
            })
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
    clubs = Club.objects.annotate(member_count=Count('memberships')).order_by('-created_at')

    if query:
        clubs = clubs.filter(
            Q(name__icontains=query) | 
            Q(unique_id__icontains=query) | 
            Q(description__icontains=query)
        )

    # Pagination
    paginator = Paginator(clubs, 12)  # Show 12 clubs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get user's clubs
    user_clubs = Club.objects.filter(memberships__user=request.user, memberships__status='active')

    return render(request, "club/club_list.html", {
        "clubs": page_obj,
        "query": query,
        "user_clubs": user_clubs
    })


@login_required
def club_detail(request, unique_id):
    """Enhanced club detail with activities and recent chats"""
    club = get_object_or_404(Club, unique_id=unique_id)
    
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    is_admin = membership and membership.role in ["owner", "admin"]
    is_member = membership is not None

    # Get recent activities and events
    recent_activities = ClubActivity.objects.filter(club=club)[:5]
    upcoming_events = ClubEvent.objects.filter(club=club, event_date__gte=timezone.now())[:3]
    recent_chats = ClubChat.objects.filter(club=club)[:10] if is_member else []
    
    # Member statistics
    member_stats = {
        'total_members': ClubMember.objects.filter(club=club, status='active').count(),
        'pending_requests': ClubMember.objects.filter(club=club, status='pending').count() if is_admin else 0
    }

    return render(request, "club/club_detail.html", {
        "club": club,
        "membership": membership,
        "is_admin": is_admin,
        "is_member": is_member,
        "recent_activities": recent_activities,
        "upcoming_events": upcoming_events,
        "recent_chats": recent_chats,
        "member_stats": member_stats
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
def club_chat(request, unique_id):
    """Club chat interface"""
    club = get_object_or_404(Club, unique_id=unique_id)
    
    # Check if user is a member
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        messages.error(request, "🚫 You must be a member to access the chat.")
        return redirect("club:club_detail", unique_id=unique_id)

    # Get chat messages
    messages_list = ClubChat.objects.filter(club=club).order_by('-created_at')[:50]
    messages_list = list(reversed(messages_list))  # Show oldest first

    # Add poll data to messages
    for message in messages_list:
        if message.is_poll:
            poll_data = message.get_poll_data()
            if poll_data:
                message.poll_data = poll_data

    chat_form = ChatMessageForm()

    return render(request, "club/chat.html", {
        "club": club,
        "messages": messages_list,
        "form": chat_form,
        "membership": membership
    })

# @login_required
# @csrf_exempt
# def send_chat_message(request, unique_id):
#     """AJAX endpoint for sending chat messages"""
#     if request.method == 'POST':
#         club = get_object_or_404(Club, unique_id=unique_id)
        
#         # Check membership
#         membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
#         if not membership:
#             return JsonResponse({'error': 'Not authorized'}, status=403)

#         data = json.loads(request.body)
#         message_text = data.get('message', '').strip()
        
#         if message_text:
#             chat_message = ClubChat.objects.create(
#                 club=club,
#                 sender=request.user,
#                 message=message_text
#             )
            
#             return JsonResponse({
#                 'success': True,
#                 'message': {
#                     'id': chat_message.id,
#                     'sender': request.user.username,
#                     'message': chat_message.message,
#                     'created_at': chat_message.created_at.strftime('%H:%M')
#                 }
#             })
    
#     return JsonResponse({'error': 'Invalid request'}, status=400)

# @login_required
# @csrf_exempt
# @require_http_methods(["POST"])
# def typing_indicator(request, unique_id):
#     """Handle typing indicators for real-time chat"""
#     club = get_object_or_404(Club, unique_id=unique_id)
    
#     # Check membership
#     membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
#     if not membership:
#         return JsonResponse({'error': 'Not authorized'}, status=403)
    
#     data = json.loads(request.body)
#     is_typing = data.get('typing', False)
    
#     # Store typing status in cache (expires in 3 seconds)
#     cache_key = f'typing_{club.id}_{request.user.id}'
#     if is_typing:
#         cache.set(cache_key, True, timeout=3)
#     else:
#         cache.delete(cache_key)
    
#     return JsonResponse({'success': True})

@login_required
def online_members(request, unique_id):
    """Get list of online members"""
    club = get_object_or_404(Club, unique_id=unique_id)
    
    # Check membership
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    # Get active members who have been online in the last 2 minutes
    two_minutes_ago = timezone.now() - timezone.timedelta(minutes=2)
    online_members = ClubMember.objects.filter(
        club=club, 
        status='active',
        user__last_login__gte=two_minutes_ago
    ).select_related('user', 'user__student_profile')
    
    # Format response
    members_data = []
    for member in online_members:
        profile = member.user.student_profile
        members_data.append({
            'id': member.user.id,
            'username': member.user.username,
            'online': True,
            'profile_image': profile.profile_image.url if profile and profile.profile_image else None,
            'initials': f"{member.user.first_name[0] if member.user.first_name else ''}{member.user.last_name[0] if member.user.last_name else ''}".upper() or member.username[0].upper()
        })
    
    return JsonResponse({
        'count': len(members_data),
        'members': members_data
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_poll(request, unique_id):
    """Create a poll in the chat"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    data = json.loads(request.body)
    question = data.get('question', '').strip()
    options = data.get('options', [])

    if not question or len(options) < 2:
        return JsonResponse({'error': 'Poll must have a question and at least 2 options'}, status=400)

    # Create poll message
    poll_message = ClubChat.objects.create(
        club=club,
        sender=request.user,
        message=f"POLL: {question}",
        is_poll=True
    )

    poll_options = []
    for option_text in options:
        opt = PollOption.objects.create(chat=poll_message, option_text=option_text)
        poll_options.append({'id': opt.id, 'text': opt.option_text, 'votes': 0, 'percentage': 0})

    return JsonResponse({
        'success': True,
        'message': {
            'id': poll_message.id,
            'sender': request.user.username,
            'created_at': poll_message.created_at.strftime('%H:%M'),
            'is_poll': True,
            'poll_data': {
                'question': question,
                'options': poll_options,
                'total_votes': 0
            }
        }
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def vote_poll(request, unique_id):
    """Vote on a poll"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    data = json.loads(request.body)
    message_id = data.get('message_id')
    option_id = data.get('option_id')

    try:
        poll_message = ClubChat.objects.get(id=message_id, club=club, is_poll=True)
        poll_option = PollOption.objects.get(id=option_id, chat=poll_message)

        # Prevent multiple votes per poll
        if PollVote.objects.filter(user=request.user, poll_option__chat=poll_message).exists():
            return JsonResponse({'error': 'You have already voted on this poll'}, status=400)

        PollVote.objects.create(user=request.user, poll_option=poll_option)
        poll_option.votes = PollVote.objects.filter(poll_option=poll_option).count()
        poll_option.save()

        # Build updated results
        total_votes = PollVote.objects.filter(poll_option__chat=poll_message).count()
        options = []
        for opt in PollOption.objects.filter(chat=poll_message):
            percentage = round((opt.votes / total_votes) * 100) if total_votes > 0 else 0
            options.append({
                'id': opt.id,
                'text': opt.option_text,
                'votes': opt.votes,
                'percentage': percentage
            })

        return JsonResponse({
            'success': True,
            'poll_data': {
                'question': poll_message.message.replace("POLL: ", ""),
                'options': options,
                'total_votes': total_votes
            }
        })

    except (ClubChat.DoesNotExist, PollOption.DoesNotExist):
        return JsonResponse({'error': 'Poll or option not found'}, status=404)

# @login_required
# def get_new_messages(request, unique_id):
#     """Get new messages since last check"""
#     club = get_object_or_404(Club, unique_id=unique_id)
    
#     # Check membership
#     membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
#     if not membership:
#         return JsonResponse({'error': 'Not authorized'}, status=403)
    
#     last_id = request.GET.get('last_id', 0)
    
#     try:
#         last_id = int(last_id)
#     except (ValueError, TypeError):
#         last_id = 0
    
#     # Get messages newer than last_id
#     new_messages = ClubChat.objects.filter(
#         club=club, 
#         id__gt=last_id
#     ).order_by('created_at')[:50]
    
#     # Format messages for JSON response
#     messages_data = []
#     for msg in new_messages:
#         message_data = {
#             'id': msg.id,
#             'sender': {
#                 'id': msg.sender.id,
#                 'username': msg.sender.username
#             },
#             'message': msg.message,
#             'created_at': msg.created_at.strftime('%H:%M'),
#             'is_poll': msg.is_poll
#         }
        
#         if msg.is_poll:
#             try:
#                 poll_data = json.loads(msg.poll_question)
#                 message_data['poll_data'] = poll_data
#             except (ValueError, TypeError):
#                 message_data['is_poll'] = False
        
#         messages_data.append(message_data)
    
#     return JsonResponse({
#         'messages': messages_data
#     })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def toggle_reaction(request, unique_id):
    """Add or remove emoji reaction on a message"""
    club = get_object_or_404(Club, unique_id=unique_id)
    membership = ClubMember.objects.filter(club=club, user=request.user, status="active").first()
    if not membership:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    data = json.loads(request.body)
    message_id = data.get('message_id')
    emoji = data.get('emoji')

    try:
        chat_message = ClubChat.objects.get(id=message_id, club=club)
    except ClubChat.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)

    from .models import ClubChatReaction

    # Check if reaction exists
    reaction, created = ClubChatReaction.objects.get_or_create(
        chat=chat_message,
        user=request.user,
        emoji=emoji
    )

    if not created:  
        # remove reaction if already exists
        reaction.delete()
        action = "removed"
    else:
        action = "added"

    # Get updated reactions
    reactions_summary = (
        ClubChatReaction.objects.filter(chat=chat_message)
        .values("emoji")
        .annotate(count=Count("id"))
    )

    return JsonResponse({
        "success": True,
        "action": action,
        "reactions": list(reactions_summary)
    })


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