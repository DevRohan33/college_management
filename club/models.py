from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid
import json

User = get_user_model()


class Club(models.Model):
    """Main Club Model"""
    name = models.CharField(max_length=255)
    unique_id = models.CharField(max_length=12, unique=True, editable=False)  # invite code
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="clubs_created")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = str(uuid.uuid4()).split("-")[0].upper()  # short unique id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.unique_id})"

class ClubMember(models.Model):
    """Membership model with roles, status, and badges"""
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("moderator", "Moderator"),
        ("member", "Member"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("banned", "Banned"),
    ]
    BADGE_CHOICES = [
        ("bronze", "Bronze"),
        ("silver", "Silver"),
        ("gold", "Gold"),
        ("platinum", "Platinum"),
        ("diamond", "Diamond"),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="club_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, default="bronze")
    points = models.IntegerField(default=0)  # for ranking
    joined_at = models.DateTimeField(auto_now_add=True)
    banned_until = models.DateTimeField(blank=True, null=True)  # for temporary bans

    class Meta:
        unique_together = ("club", "user")  # one user cannot join same club twice

    def __str__(self):
        return f"{self.user.username} in {self.club.name} ({self.role})"


#------------------club activities & events models------------------
class ClubActivity(models.Model):
    """Activity feed for posts/announcements"""
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="activities")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Activity in {self.club.name} by {self.created_by.username}"

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()


class ActivityLike(models.Model):
    """Likes on an activity"""
    activity = models.ForeignKey(ClubActivity, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("activity", "user")  # a user can like only once

    def __str__(self):
        return f"{self.user.username} liked {self.activity.id}"


class ActivityComment(models.Model):
    """Comments on an activity"""
    activity = models.ForeignKey(ClubActivity, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on activity {self.activity.id}"

class ClubEvent(models.Model):
    """Events inside a club"""
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["event_date"]

    def __str__(self):
        return f"{self.title} ({self.club.name})"

class EventRSVP(models.Model):
    RSVP_CHOICES = [
        ('yes', 'Going'),
        ('maybe', 'Maybe'),
        ('no', "Can't Go"),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rsvps")
    event = models.ForeignKey(ClubEvent, on_delete=models.CASCADE, related_name="rsvps")
    response = models.CharField(max_length=10, choices=RSVP_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'event'], name="unique_user_event_rsvp")
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.response})"
    
#------------------club chat models------------------


class ClubChat(models.Model):
    """Chat messages inside each club"""
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="chats")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_poll = models.BooleanField(default=False)
    poll_question = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"
   
    def get_poll_data(self):
        if self.is_poll and self.poll_question:
            try:
                return json.loads(self.poll_question)
            except:
                return None
        return None
    
class PollOption(models.Model):
    chat = models.ForeignKey(ClubChat, on_delete=models.CASCADE, related_name='poll_options')
    option_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.option_text} ({self.votes} votes)"
    
class PollVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    poll_option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'poll_option')
    
    def __str__(self):
        return f"{self.user.username} voted for {self.poll_option.option_text}"
    

class ClubChatReaction(models.Model):
    chat = models.ForeignKey(ClubChat, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)  #  👍, ❤️, 😂
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("chat", "user", "emoji")  # one emoji per user per chat

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to {self.chat.id}"
