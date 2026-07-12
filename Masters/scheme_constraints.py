from __future__ import annotations

from typing import Dict, List

from Masters.models import Scheme, SchemeCondition, SchemeBenefit


SCHEME_TYPE_CONSTRAINTS: Dict[str, Dict[str, List[str]]] = {
    Scheme.SchemeType.QUANTITY: {
        "condition_types": [
            SchemeCondition.ConditionType.MIN_QUANTITY,
            SchemeCondition.ConditionType.MAX_QUANTITY,
            SchemeCondition.ConditionType.EXACT_QUANTITY,
            SchemeCondition.ConditionType.QUANTITY_RANGE,
        ],
        "benefit_types": [
            SchemeBenefit.BenefitType.DISCOUNT_PERCENTAGE,
            SchemeBenefit.BenefitType.DISCOUNT_AMOUNT,
            SchemeBenefit.BenefitType.FREE_ITEM,
            SchemeBenefit.BenefitType.FREE_QUANTITY,
            SchemeBenefit.BenefitType.CASHBACK,
        ],
    },
    Scheme.SchemeType.VALUE: {
        "condition_types": [
            SchemeCondition.ConditionType.MIN_VALUE,
            SchemeCondition.ConditionType.MAX_VALUE,
            SchemeCondition.ConditionType.VALUE_RANGE,
        ],
        "benefit_types": [
            SchemeBenefit.BenefitType.DISCOUNT_PERCENTAGE,
            SchemeBenefit.BenefitType.DISCOUNT_AMOUNT,
            SchemeBenefit.BenefitType.CASHBACK,
        ],
    },
    Scheme.SchemeType.COMBO: {
        "condition_types": [
            SchemeCondition.ConditionType.ITEM_COMBO,
        ],
        "benefit_types": [
            SchemeBenefit.BenefitType.FREE_ITEM,
            SchemeBenefit.BenefitType.FREE_QUANTITY,
            SchemeBenefit.BenefitType.DISCOUNT_AMOUNT,
            SchemeBenefit.BenefitType.DISCOUNT_PERCENTAGE,
        ],
    },
    Scheme.SchemeType.SLAB: {
        "condition_types": [
            SchemeCondition.ConditionType.QUANTITY_RANGE,
            SchemeCondition.ConditionType.VALUE_RANGE,
            SchemeCondition.ConditionType.MAX_QUANTITY,
            SchemeCondition.ConditionType.MAX_VALUE,
        ],
        "benefit_types": [
            SchemeBenefit.BenefitType.DISCOUNT_PERCENTAGE,
            SchemeBenefit.BenefitType.DISCOUNT_AMOUNT,
            SchemeBenefit.BenefitType.FREE_ITEM,
            SchemeBenefit.BenefitType.FREE_QUANTITY,
            SchemeBenefit.BenefitType.CASHBACK,
        ],
    },
    Scheme.SchemeType.FLAT: {
        "condition_types": [
            SchemeCondition.ConditionType.MIN_VALUE,
            SchemeCondition.ConditionType.MIN_QUANTITY,
            SchemeCondition.ConditionType.MAX_VALUE,
            SchemeCondition.ConditionType.MAX_QUANTITY,
        ],
        "benefit_types": [
            SchemeBenefit.BenefitType.DISCOUNT_AMOUNT,
            SchemeBenefit.BenefitType.CASHBACK,
        ],
    },
}


def get_allowed_condition_types(scheme_type: str) -> List[str]:
    return SCHEME_TYPE_CONSTRAINTS.get(scheme_type, {}).get("condition_types", [])


def get_allowed_benefit_types(scheme_type: str) -> List[str]:
    return SCHEME_TYPE_CONSTRAINTS.get(scheme_type, {}).get("benefit_types", [])


def get_scheme_type_constraints(scheme_type: str) -> Dict[str, List[str]]:
    return SCHEME_TYPE_CONSTRAINTS.get(scheme_type, {})
