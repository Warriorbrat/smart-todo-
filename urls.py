from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, ContextEntryViewSet, CategoryViewSet

router = DefaultRouter()
router.register('tasks', TaskViewSet)
router.register('context', ContextEntryViewSet)
router.register('categories', CategoryViewSet)

urlpatterns = router.urls
