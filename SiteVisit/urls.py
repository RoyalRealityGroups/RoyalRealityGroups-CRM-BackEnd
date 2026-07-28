from rest_framework.routers import DefaultRouter
from .views import SiteVisitViewSet, CalendarTodoViewSet

router = DefaultRouter()
router.register(r'site-visits', SiteVisitViewSet, basename='site-visit')
router.register(r'todos', CalendarTodoViewSet, basename='calendar-todo')

urlpatterns = router.urls
