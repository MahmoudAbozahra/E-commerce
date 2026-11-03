from django.db import transaction
from rest_framework.exceptions import ValidationError

from account.models import AuditLog

from .models import InventoryMovement, ProductVariant


@transaction.atomic
def adjust_inventory(*, variant: ProductVariant, delta: int, actor, reason: str) -> InventoryMovement:
    """Apply one audited stock delta while holding the variant row lock."""
    variant = ProductVariant.objects.select_for_update().get(pk=variant.pk)
    if delta == 0 or variant.stock + delta < 0:
        raise ValidationError({"delta": "Adjustment must be non-zero and cannot make stock negative."})
    variant.stock += delta
    variant.save(update_fields=("stock", "updated_at"))
    movement = InventoryMovement.objects.create(
        variant=variant,
        delta=delta,
        reason=InventoryMovement.Reason.ADJUST,
        actor=actor,
        reference=reason,
    )
    AuditLog.objects.create(
        actor=actor,
        action="inventory.adjust",
        entity_type="variant",
        entity_id=str(variant.pk),
        details={"delta": delta, "reason": reason},
    )
    return movement
