from django.db import models

class ContactSubmission(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    service_interest = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.service_interest}"

class QuotationSubmission(models.Model):
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, default='')
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    services = models.TextField()
    timeline = models.CharField(max_length=100)
    budget = models.CharField(max_length=100)
    features = models.TextField(blank=True, default='')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Proposal: {self.name} ({self.company or 'Individual'})"
