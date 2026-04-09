from django.contrib import admin
from .models import Student, Mark, Attendance
from .models import Subject


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'roll_no',
        'semester',
        'link_status',
        'linked_user'
    )

    list_filter = ('semester',)
    search_fields = ('name', 'roll_no')

    # 🟢 / 🔴 Link Status
    def link_status(self, obj):
        return "🟢 Linked" if obj.user else "🔴 Not Linked"
    link_status.short_description = "Status"

    # Show linked username
    def linked_user(self, obj):
        return obj.user.username if obj.user else "-"
    linked_user.short_description = "User"


admin.site.register(Mark)
admin.site.register(Attendance)
admin.site.register(Subject)
