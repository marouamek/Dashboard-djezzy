from django.contrib import admin
from .models import Profile

# Register the Profile model with the Django admin site
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  # Show username and role in the list