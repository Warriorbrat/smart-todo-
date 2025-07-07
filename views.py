# tasks/views.py
import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Task, Category
from .serializers import TaskSerializer, CategorySerializer
from ai_integration.ai_module import AITaskManagement # Import your AI module
from context.models import ContextEntry # To fetch daily context for AI

# Initialize AI manager once (or you can initialize per request in a more complex setup)
# For simplicity, we'll initialize it here. You might want to pass the API choice
# from Django settings if you have multiple choices.
ai_manager = AITaskManagement(api_choice=os.getenv("AI_API_CHOICE", "openai")) # Default to OpenAI

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Task API operations.
    Provides CRUD operations and AI-powered task suggestions/re-evaluation.
    """
    queryset = Task.objects.all().order_by('-created_at') # Default queryset, ordered by creation date
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        Ensures that users can only see and manage their own tasks.
        """
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Custom create operation to integrate AI suggestions.
        When a new task is created, AI generates priority, deadline, and other suggestions.
        """
        # 1. Save the task initially with the user assigned.
        # This allows us to get a task instance with an ID before AI processing.
        task = serializer.save(user=self.request.user)

        # 2. Fetch all relevant context entries for the current user for AI analysis.
        daily_context_data = list(ContextEntry.objects.filter(user=self.request.user).values('content', 'source_type'))

        # 3. Prepare AI input parameters.
        # Placeholder for user preferences (fetch from UserPreference model if implemented)
        user_preferences = {}
        # Calculate current task load (number of pending tasks for the user)
        current_task_load = Task.objects.filter(user=self.request.user, status='pending').count()

        # 4. Call the AI module to get suggestions.
        ai_suggestions = ai_manager.get_task_suggestions(
            task_details={
                'title': task.title,
                'description': task.description,
                'category': task.category.name if task.category else None # Pass category name if available
            },
            daily_context_data=daily_context_data,
            user_preferences=user_preferences,
            current_task_load=current_task_load
        )

        # 5. Update the task instance with AI-generated data.
        task.priority_score = ai_suggestions.get('priority_score', 0)
        task.deadline = ai_suggestions.get('deadline') # This will be a datetime object or None
        task.ai_suggestions = ai_suggestions # Store the full JSON output from AI
        task.save() # Save the updated task

    def perform_update(self, serializer):
        """
        Custom update operation.
        AI re-evaluation is handled by a separate action (`re_evaluate_ai`).
        """
        # Ensure the task remains associated with the current user
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='re-evaluate-ai')
    def re_evaluate_ai(self, request, pk=None):
        """
        Custom action to re-evaluate AI suggestions for an existing task.
        This allows the frontend to trigger AI analysis on demand, e.g., after context changes.
        """
        task = self.get_object() # Get the specific task instance based on URL ID

        # Fetch current daily context for the user
        daily_context_data = list(ContextEntry.objects.filter(user=self.request.user).values('content', 'source_type'))

        # Placeholder for user preferences and current task load
        user_preferences = {}
        current_task_load = Task.objects.filter(user=self.request.user, status='pending').count()

        # Call AI for updated suggestions
        ai_suggestions = ai_manager.get_task_suggestions(
            task_details={
                'title': task.title,
                'description': task.description,
                'category': task.category.name if task.category else None
            },
            daily_context_data=daily_context_data,
            user_preferences=user_preferences,
            current_task_load=current_task_load
        )

        # Update task fields with new AI suggestions (only if AI provided them, otherwise keep existing)
        task.priority_score = ai_suggestions.get('priority_score', task.priority_score)
        task.deadline = ai_suggestions.get('deadline', task.deadline)
        task.ai_suggestions = ai_suggestions
        task.save()

        # Return the updated task data
        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Category API operations.
    Provides CRUD for categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        """
        Allows users to see their own categories and any categories not assigned to a specific user (global).
        """
        # This assumes some categories might be system-wide (user=None) and others user-specific.
        return self.queryset.filter(user=self.request.user) | self.queryset.filter(user__isnull=True)

    def perform_create(self, serializer):
        """
        Assigns the creating user to the new category.
        """
        serializer.save(user=self.request.user)