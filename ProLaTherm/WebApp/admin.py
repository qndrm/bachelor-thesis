from django.contrib import admin
from .models import ProteinSequence, UserRequest,RequestStatistics

class UserRequestAdmin(admin.ModelAdmin):
    readonly_fields = ['hash','number_of_sequences','created_at','email']
    ordering = ['-created_at']

admin.site.register(ProteinSequence)
admin.site.register(UserRequest, UserRequestAdmin)
admin.site.register(RequestStatistics)
