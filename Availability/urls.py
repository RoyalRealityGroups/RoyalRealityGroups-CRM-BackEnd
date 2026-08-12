from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AvailabilityProjectViewSet,
    AvailabilityBlockViewSet,
    AvailabilityUnitViewSet,
    AvailabilityProjectImageDetailView,
)

router = DefaultRouter()
router.register(r'projects', AvailabilityProjectViewSet, basename='avail-project')
router.register(r'blocks',   AvailabilityBlockViewSet,   basename='avail-block')
router.register(r'units',    AvailabilityUnitViewSet,    basename='avail-unit')

urlpatterns = [
    path('', include(router.urls)),
    # Single-image CRUD (retrieve / update title / delete)
    path('images/<str:pk>/', AvailabilityProjectImageDetailView.as_view(), name='avail-image-detail'),
]

# Resulting endpoints (all under /api/availability/):
#
# Projects
#   GET    /api/availability/projects/              list (lightweight)
#   POST   /api/availability/projects/              create
#   GET    /api/availability/projects/choices/      all dropdowns
#   GET    /api/availability/projects/{id}/         detail (full w/ blocks+images)
#   PUT    /api/availability/projects/{id}/         update
#   PATCH  /api/availability/projects/{id}/         partial update
#   DELETE /api/availability/projects/{id}/         soft-delete
#   GET    /api/availability/projects/{id}/stats/   unit count breakdown
#   POST   /api/availability/projects/{id}/images/upload/  bulk image upload
#
# Blocks
#   GET    /api/availability/blocks/                list (filter by ?project=)
#   POST   /api/availability/blocks/                create
#   GET    /api/availability/blocks/{id}/           detail (with nested units)
#   PUT    /api/availability/blocks/{id}/           update
#   DELETE /api/availability/blocks/{id}/           soft-delete
#   GET    /api/availability/blocks/{id}/units/     all units for block
#   POST   /api/availability/blocks/{id}/bulk_units/ atomic bulk create
#   GET    /api/availability/blocks/{id}/stats/     unit counts
#
# Units
#   GET    /api/availability/units/                 list (filter by ?block=, ?status=)
#   POST   /api/availability/units/                 create single unit
#   GET    /api/availability/units/{id}/            detail
#   PUT    /api/availability/units/{id}/            update
#   DELETE /api/availability/units/{id}/            soft-delete
#   PATCH  /api/availability/units/{id}/update_status/  quick status change
#
# Images
#   GET/PUT/DELETE /api/availability/images/{id}/   single image ops
