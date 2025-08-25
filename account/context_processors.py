from teacher.models import TeacherProfile

def profile_context(request):
    if request.user.is_authenticated and hasattr(request.user, "teacherprofile"):
        return {"profile": request.user.teacherprofile}
    return {}
