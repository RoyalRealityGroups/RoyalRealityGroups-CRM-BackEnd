from django.urls import path
from .views import (
    ProofOfDeliveryListCreateView,
    ProofOfDeliveryDetailView,
    ProofOfDeliveryFileDeleteView,
    GeneratePODNumber,
    AvailableCustomersForPODView,
    ProofOfDeliveryStatusCountView,
)

urlpatterns = [
    path('proofs/', ProofOfDeliveryListCreateView.as_view(), name='pod-list'),
    path('proofs/status-count/', ProofOfDeliveryStatusCountView.as_view(), name='pod-status-count'),
    path('proofs/available-customers/', AvailableCustomersForPODView.as_view(), name='pod-available-customers'),
    path('proofs/generate-pod-number/', GeneratePODNumber.as_view(), name='generate-pod-number'),
    path('proofs/<uuid:pk>/', ProofOfDeliveryDetailView.as_view(), name='pod-detail'),
    path('proofs/<uuid:pk>/files/<uuid:file_id>/', ProofOfDeliveryFileDeleteView.as_view(), name='pod-file-delete'),
]
