from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from django.core.management.base import BaseCommand
from django.utils import timezone

from Masters.models import (
    Scheme,
    SchemeCondition,
    SchemeBenefit,
    SchemeApplicability,
    SchemeItem,
    Item,
    Company,
)


class Command(BaseCommand):
    help = "Seed multiple scheme records covering all scheme types."

    def add_arguments(self, parser):
        parser.add_argument(
            "--company-id",
            dest="company_id",
            help="Company UUID to attach schemes to (optional).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing seeded schemes before creating.",
        )

    def handle(self, *args, **options):
        company_id = options.get("company_id")
        clear_existing = options.get("clear", False)

        company = Company.objects.filter(id=company_id).first() if company_id else Company.objects.first()
        if not company:
            self.stderr.write(self.style.ERROR("No Company found. Create a company first."))
            return

        items = list(Item.objects.all()[:4])
        if len(items) < 2:
            self.stderr.write(self.style.ERROR("Need at least 2 items to seed schemes."))
            return

        item_a = items[0]
        item_b = items[1]
        item_c = items[2] if len(items) > 2 else items[0]

        today = timezone.now().date()

        seed_codes = [
            "SEED-QTY-001",
            "SEED-VAL-001",
            "SEED-COMBO-001",
            "SEED-SLAB-001",
            "SEED-FLAT-001",
        ]

        if clear_existing:
            Scheme.objects.filter(code__in=seed_codes).delete()

        def upsert_scheme(
            code: str,
            name: str,
            scheme_type: str,
            priority: int,
        ) -> Scheme:
            scheme, created = Scheme.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": f"Seeded scheme: {name}",
                    "scheme_type": scheme_type,
                    "status": Scheme.Status.ACTIVE,
                    "priority": priority,
                    "is_stackable": True,
                    "effective_from": today,
                    "effective_to": None,
                    "company": company,
                },
            )
            if not created:
                scheme.name = name
                scheme.scheme_type = scheme_type
                scheme.status = Scheme.Status.ACTIVE
                scheme.priority = priority
                scheme.is_stackable = True
                scheme.effective_from = today
                scheme.effective_to = None
                scheme.company = company
                scheme.save()

            SchemeCondition.objects.filter(scheme=scheme).delete()
            SchemeBenefit.objects.filter(scheme=scheme).delete()
            SchemeApplicability.objects.filter(scheme=scheme).delete()
            SchemeItem.objects.filter(scheme=scheme).delete()
            return scheme

        def add_applicability(scheme: Scheme):
            SchemeApplicability.objects.create(
                scheme=scheme,
                customer_type="ALL",
                apply_to_all=True,
            )

        # QUANTITY
        scheme_qty = upsert_scheme(
            code="SEED-QTY-001",
            name="Quantity Based 5% Off",
            scheme_type=Scheme.SchemeType.QUANTITY,
            priority=10,
        )
        SchemeCondition.objects.create(
            scheme=scheme_qty,
            condition_type=SchemeCondition.ConditionType.MIN_QUANTITY,
            value_from=Decimal("10"),
            logical_operator="AND",
        )
        SchemeBenefit.objects.create(
            scheme=scheme_qty,
            benefit_type=SchemeBenefit.BenefitType.DISCOUNT_PERCENTAGE,
            discount_value=Decimal("5"),
            apply_to_all=True,
        )
        SchemeItem.objects.create(scheme=scheme_qty, include_all_items=True)
        add_applicability(scheme_qty)

        # VALUE
        scheme_val = upsert_scheme(
            code="SEED-VAL-001",
            name="Value Based ₹100 Off",
            scheme_type=Scheme.SchemeType.VALUE,
            priority=20,
        )
        SchemeCondition.objects.create(
            scheme=scheme_val,
            condition_type=SchemeCondition.ConditionType.MIN_VALUE,
            value_from=Decimal("1000"),
            logical_operator="AND",
        )
        SchemeBenefit.objects.create(
            scheme=scheme_val,
            benefit_type=SchemeBenefit.BenefitType.DISCOUNT_AMOUNT,
            discount_value=Decimal("100"),
            apply_to_all=True,
        )
        SchemeItem.objects.create(scheme=scheme_val, include_all_items=True)
        add_applicability(scheme_val)

        # COMBO
        scheme_combo = upsert_scheme(
            code="SEED-COMBO-001",
            name="Combo Offer: Buy A+B Get C Free",
            scheme_type=Scheme.SchemeType.COMBO,
            priority=30,
        )
        SchemeCondition.objects.create(
            scheme=scheme_combo,
            condition_type=SchemeCondition.ConditionType.ITEM_COMBO,
            item=item_a,
            logical_operator="AND",
        )
        SchemeCondition.objects.create(
            scheme=scheme_combo,
            condition_type=SchemeCondition.ConditionType.ITEM_COMBO,
            item=item_b,
            logical_operator="AND",
        )
        SchemeBenefit.objects.create(
            scheme=scheme_combo,
            benefit_type=SchemeBenefit.BenefitType.FREE_ITEM,
            free_item=item_c,
            free_quantity=Decimal("1"),
        )
        SchemeItem.objects.create(scheme=scheme_combo, item=item_a)
        SchemeItem.objects.create(scheme=scheme_combo, item=item_b)
        add_applicability(scheme_combo)

        # SLAB
        scheme_slab = upsert_scheme(
            code="SEED-SLAB-001",
            name="Slab 5-10 Qty 7.5% Off",
            scheme_type=Scheme.SchemeType.SLAB,
            priority=40,
        )
        SchemeCondition.objects.create(
            scheme=scheme_slab,
            condition_type=SchemeCondition.ConditionType.QUANTITY_RANGE,
            value_from=Decimal("5"),
            value_to=Decimal("10"),
            logical_operator="AND",
        )
        SchemeBenefit.objects.create(
            scheme=scheme_slab,
            benefit_type=SchemeBenefit.BenefitType.DISCOUNT_PERCENTAGE,
            discount_value=Decimal("7.5"),
            apply_to_all=True,
        )
        SchemeItem.objects.create(scheme=scheme_slab, include_all_items=True)
        add_applicability(scheme_slab)

        # FLAT
        scheme_flat = upsert_scheme(
            code="SEED-FLAT-001",
            name="Flat ₹200 Off on ₹2000+",
            scheme_type=Scheme.SchemeType.FLAT,
            priority=50,
        )
        SchemeCondition.objects.create(
            scheme=scheme_flat,
            condition_type=SchemeCondition.ConditionType.MIN_VALUE,
            value_from=Decimal("2000"),
            logical_operator="AND",
        )
        SchemeBenefit.objects.create(
            scheme=scheme_flat,
            benefit_type=SchemeBenefit.BenefitType.DISCOUNT_AMOUNT,
            discount_value=Decimal("200"),
            apply_to_all=True,
        )
        SchemeItem.objects.create(scheme=scheme_flat, include_all_items=True)
        add_applicability(scheme_flat)

        self.stdout.write(self.style.SUCCESS("Seeded schemes successfully."))
