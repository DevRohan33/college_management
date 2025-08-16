from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, Semester


# Customizing the User Admin
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'get_full_name', 'role', 'department', 'semester')
    list_filter = ('role', 'department', 'semester')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role & Department', {'fields': ('role', 'department', 'semester')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'role', 'department', 'semester', 'password1', 'password2'),
        }),
    )


# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Semester)
