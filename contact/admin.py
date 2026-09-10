from django.contrib import admin
from .models import ContactSubmission, QuotationSubmission

@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'service_interest', 'created_at')
    search_fields = ('name', 'email', 'service_interest')
    list_filter = ('service_interest', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(QuotationSubmission)
class QuotationSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'timeline', 'budget', 'created_at')
    search_fields = ('name', 'company', 'email', 'phone', 'services')
    list_filter = ('timeline', 'budget', 'created_at')
    readonly_fields = ('created_at',)
