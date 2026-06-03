from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Store, Product
from .serializers import StoreSerializer, ProductSerializer

logger = logging.getLogger(__name__)

_MERCH_PROMPT = (
    "You are Merch, an AI eCommerce optimization specialist. "
    "Rewrite the product description to be compelling and SEO-friendly, and suggest an optimal price. "
    "Return a JSON object with keys: 'ai_description' (string) and 'ai_price' (float)."
)


class StoreViewSet(viewsets.ModelViewSet):
    serializer_class = StoreSerializer
    queryset = Store.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Store.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Product.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="optimize")
    def optimize(self, request, pk=None):
        """POST /api/v1/merch/products/<pk>/optimize/ — AI rewrites description and suggests price."""
        product = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Product: {product.title}\n"
            f"SKU: {product.sku}\n"
            f"Current Price: {product.price}\n"
            f"Units Sold (30d): {product.units_sold_30d}\n"
            f"Store Platform: {product.store.platform}\n"
            f"Currency: {product.store.currency}"
        )
        try:
            raw = ai_chat(
                system_prompt=_MERCH_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            data = json.loads(raw)
            product.ai_description = data.get("ai_description", raw)
            product.ai_price = data.get("ai_price")
            product.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="merch_optimize_product", resource=f"Product/{product.id}",
                status="ALLOWED", inspector_reason="AI product optimized",
                rules_triggered=[], raw_request_payload={"product_id": str(product.id)},
            )
            return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Merch optimize failed for product %s: %s", product.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="merch_optimize_product", resource=f"Product/{product.id}",
                status="BLOCKED", inspector_reason=f"Product optimization failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
