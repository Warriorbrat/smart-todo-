

# Create your # tasks/models.py
from django.db import models
from django.contrib.auth.models import User # Django's built-in User model
import uuid # For UUID primary keys

# Category Model
class Category(models.Model):
    # Using UUID as primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Optional: If categories can be user-specific. If global, remove `user`.
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    usage_frequency = models.IntegerField(default=0) # To track how often a category is used
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories" # Correct plural name in admin

    def __str__(self):
        return self.name

# Task Model
class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Each task belongs to a user
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True) # Description can be empty
    # ForeignKey to Category, allows null if a task doesn't have a category
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority_score = models.IntegerField(default=0) # AI-generated score (e.g., 1-100)
    deadline = models.DateTimeField(blank=True, null=True) # Deadline can be null
    status = models.CharField(max_length=50, default='pending') # e.g., 'pending', 'in_progress', 'completed'
    ai_suggestions = models.JSONField(blank=True, null=True) # Store AI suggestions (like enhanced description, etc.)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Automatically updates on each save

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at'] # Default ordering for tasksmodels here.
