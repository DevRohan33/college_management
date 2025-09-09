document.addEventListener('DOMContentLoaded', function() {
    // Auto-resize textarea
    const textarea = document.querySelector('#id_content');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
});

// Toggle comments section
function toggleComments(activityId) {
    const commentsDiv = document.getElementById(`comments-${activityId}`);
    if (commentsDiv.style.display === 'none') {
        commentsDiv.style.display = 'block';
        commentsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        commentsDiv.style.display = 'none';
    }
}

// CSRF helper (Django standard)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Like/unlike function
function likeActivity(activityId) {
    const csrftoken = getCookie('csrftoken');

    fetch(`/clubs/activity/${activityId}/like/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken,
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(response => response.text())  // your view redirects, so we just reload count manually
    .then(() => {
        const btn = document.querySelector(`#like-btn-${activityId} span`);
        if (btn) {
            // update like count dynamically by fetching latest from server (optional: simplest: reload page)
            location.reload();  // or you can implement ActivityLike count fetch for smoother UX
        }
    })
    .catch(err => console.error(err));
}


// Share activity (placeholder)
function shareActivity(activityId) {
    const shareText = `Check out this activity from {{ club.name }}!`;
    const clubUrl = window.location.origin + '{% url "club:club_detail" club.unique_id %}';
    
    if (navigator.share) {
        navigator.share({
            title: 'Club Activity - {{ club.name }}',
            text: shareText,
            url: clubUrl
        });
    } else {
        navigator.clipboard.writeText(clubUrl).then(() => {
            alert('Club link copied to clipboard!');
        });
    }
}

// Edit activity (placeholder)
function editActivity(activityId) {
    alert('Edit feature coming soon!');
}

// Delete activity (placeholder)
function deleteActivity(activityId) {
    if (confirm('Are you sure you want to delete this activity?')) {
        alert('Delete feature coming soon!');
    }
}

// Share club
function shareClub() {
    const clubUrl = window.location.origin + '{% url "club:club_detail" club.unique_id %}';
    const shareText = `Check out this club: {{ club.name }} ({{ club.unique_id }})`;
    
    if (navigator.share) {
        navigator.share({
            title: '{{ club.name }} - ClubHub',
            text: shareText,
            url: clubUrl
        });
    } else {
        navigator.clipboard.writeText(clubUrl).then(() => {
            alert('Club link copied to clipboard!');
        });
    }
}

// Real-time updates (placeholder)
function checkForNewActivities() {
    // This would fetch new activities via AJAX
    // You might want to implement WebSocket for real-time updates
}

// Check for new activities every 30 seconds
setInterval(checkForNewActivities, 30000);
