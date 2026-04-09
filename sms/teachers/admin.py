from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'subject',
        'link_status',
        'linked_user'
    )

    # 🟢 / 🔴 Link Status
    def link_status(self, obj):
        return "🟢 Linked" if obj.user else "🔴 Not Linked"
    link_status.short_description = "Status"

    # Show linked username
    def linked_user(self, obj):
        return obj.user.username if obj.user else "-"
    linked_user.short_description = "User"
