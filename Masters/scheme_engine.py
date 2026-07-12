"""
Scheme Engine - Core business logic for evaluating and applying promotional schemes.

This module handles:
1. Getting applicable schemes for orders
2. Validating scheme conditions (quantity, value, item combos, etc.)
3. Calculating benefits (discounts, free items, etc.)
4. Applying schemes to sales orders
"""

from decimal import Decimal
from datetime import date
from typing import List, Dict, Tuple, Optional, Any
from Masters.models import Scheme, SchemeCondition, SchemeBenefit
from django.db import models
from Sales.models import SalesOrder, SalesOrderItem, SalesOrderScheme, SalesOrderItemScheme



class SchemeEngine:
    """
    Engine to evaluate and apply promotional schemes.
    
    Usage:
        engine = SchemeEngine()
        applicable = engine.get_applicable_schemes(order)
        benefits = engine.calculate_benefits(scheme, order)
        engine.apply_schemes(order, [scheme1, scheme2])
    """
    
    def __init__(self):
        """Initialize the scheme engine"""
        self.errors = []
        self.warnings = []
    
    def get_applicable_schemes(self, order: SalesOrder, order_date: Optional[date] = None) -> List[Scheme]:
        """
        Get list of applicable schemes for a given sales order.
        
        Args:
            order: SalesOrder instance
            order_date: Override order date (default: today)
        
        Returns:
            List of applicable Scheme instances
        """
        if not order_date:
            order_date = date.today()
        
        applicable_schemes = []
        
        # Get all active schemes for the company (or schemes without a company - apply to all)
        schemes = Scheme.objects.filter(
            models.Q(company=order.company) | models.Q(company__isnull=True),
            status='ACTIVE',
            is_deleted=False,
            authorized_status=2,
            effective_from__lte=order_date
        ).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=order_date)
        ).prefetch_related(
            'applicability',
            'items',
            'conditions',
            'benefits'
        ).order_by('priority')
        
        for scheme in schemes:
            if self._is_scheme_applicable(scheme, order):
                applicable_schemes.append(scheme)
        
        return applicable_schemes
    
    def _is_scheme_applicable(self, scheme: Scheme, order: SalesOrder) -> bool:
        """
        Check if a scheme is applicable to an order.
        
        Args:
            scheme: Scheme instance
            order: SalesOrder instance
        
        Returns:
            Boolean - True if scheme is applicable
        """
        # Check geographic applicability
        geo_check = self._check_geographic_applicability(scheme, order)
        if not geo_check:
            return False
        
        # Check channel applicability
        channel_check = self._check_channel_applicability(scheme, order)
        if not channel_check:
            return False
        
        # Check item applicability
        item_check = self._check_item_applicability(scheme, order)
        if not item_check:
            return False
        
        # All checks passed
        return True
    
    def _check_geographic_applicability(self, scheme: Scheme, order: SalesOrder) -> bool:
        """Check if scheme applies to order's geographic location"""
        # Use billing address for location
        applicabilities = scheme.applicability.all()
        
        if applicabilities.exists():
            geo_match = False
            
            for applicability in applicabilities:
                # Check if location matches
                if applicability.state_id and applicability.state_id == order.billing_state_id:
                    geo_match = True
                    break
                elif applicability.city_id and applicability.city_id == order.billing_city_id:
                    geo_match = True
                    break
                elif applicability.area_id and applicability.area_id == order.billing_area_id:
                    geo_match = True
                    break
                elif not applicability.state_id and not applicability.city_id and not applicability.area_id:
                    # No geographic restrictions
                    geo_match = True
                    break
            
            if not geo_match:
                return False
        
        return True
    
    def _check_channel_applicability(self, scheme: Scheme, order: SalesOrder) -> bool:
        """Check if scheme applies to order's customer type"""
        applicabilities = scheme.applicability.all()
        
        if applicabilities.exists():
            channel_match = False
            customer_type = order.customer_type.upper()
            customer_obj = order.customer  # Get customer from property
            
            for applicability in applicabilities:
                if applicability.customer_type == 'ALL':
                    channel_match = True
                    break
                elif applicability.customer_type == customer_type:
                    # Check if specific customer is included or all are included
                    field_name = f'{order.customer_type.lower()}'
                    specific_customer = getattr(applicability, field_name, None)
                    
                    if specific_customer is None or specific_customer == customer_obj:
                        channel_match = True
                        break
            
            if not channel_match:
                return False
        
        return True
    
    def _check_item_applicability(self, scheme: Scheme, order: SalesOrder) -> bool:
        """Check if scheme applies to order's items"""
        scheme_items = scheme.items.all()
        
        if scheme_items.exists():
            # Check if scheme applies to all items
            if scheme_items.filter(include_all_items=True).exists():
                return True
            
            item_match = False
            order_item_ids = set(order.items.values_list('item_id', flat=True))
            scheme_item_ids = set(scheme_items.filter(item_id__isnull=False).values_list('item_id', flat=True))
            
            # Check if any order item is in scheme items
            if order_item_ids & scheme_item_ids:
                item_match = True
            
            # Also check categories
            if not item_match:
                scheme_category_ids = set(scheme_items.filter(category_id__isnull=False).values_list('category_id', flat=True))
                order_category_ids = set(order.items.values_list('category_id', flat=True).distinct())
                if order_category_ids & scheme_category_ids:
                    item_match = True
            
            if not item_match:
                return False
        
        return True
    
    def validate_conditions(self, scheme: Scheme, order: SalesOrder, order_items: Optional[List[SalesOrderItem]] = None) -> Tuple[bool, List[SchemeCondition], List[SchemeCondition]]:
        """
        Validate if order meets all scheme conditions.
        
        Args:
            scheme: Scheme instance
            order: SalesOrder instance
            order_items: List of SalesOrderItem instances (optional, fetched from order if not provided)
        
        Returns:
            Tuple: (is_valid: bool, matching_conditions: list, failed_conditions: list)
        """
        if order_items is None:
            order_items = list(order.items.all()) if hasattr(order, 'items') else []
        
        matching_conditions = []
        failed_conditions = []
        
        conditions = scheme.conditions.all()
        
        if not conditions.exists():
            # No conditions = scheme always applies
            return True, [], []
        
        # Get logical operator (AND/OR)
        logical_operator = conditions.first().logical_operator if conditions.first() else 'AND'
        
        for condition in conditions:
            is_valid = self._validate_condition(condition, order, order_items)
            
            if is_valid:
                matching_conditions.append(condition)
            else:
                failed_conditions.append(condition)
        
        # Evaluate based on logical operator
        if logical_operator == 'AND':
            # All conditions must be met
            all_valid = len(failed_conditions) == 0
        else:  # OR
            # At least one condition must be met
            all_valid = len(matching_conditions) > 0
        
        return all_valid, matching_conditions, failed_conditions
    
    def _validate_condition(self, condition: SchemeCondition, order: SalesOrder, order_items: List[SalesOrderItem]) -> bool:
        """
        Validate a single scheme condition.
        
        Args:
            condition: SchemeCondition instance
            order: SalesOrder instance
            order_items: List of SalesOrderItem instances
        
        Returns:
            Boolean - True if condition is met
        """
        condition_type = condition.condition_type
        
        if condition_type == 'MIN_QUANTITY':
            total_quantity = sum(
                item.quantity for item in order_items 
                if not condition.item_id or item.item_id == condition.item_id
            )
            return total_quantity >= condition.value_from
        
        elif condition_type == 'MIN_VALUE':
            total_value = sum(
                item.line_total for item in order_items 
                if not condition.item_id or item.item_id == condition.item_id
            ) or Decimal('0')
            return total_value >= condition.value_from

        elif condition_type == 'MAX_QUANTITY':
            total_quantity = sum(
                item.quantity for item in order_items
                if not condition.item_id or item.item_id == condition.item_id
            )
            return total_quantity <= condition.value_from

        elif condition_type == 'MAX_VALUE':
            total_value = sum(
                item.line_total for item in order_items
                if not condition.item_id or item.item_id == condition.item_id
            ) or Decimal('0')
            return total_value <= condition.value_from
        
        elif condition_type == 'QUANTITY_RANGE':
            total_quantity = sum(
                item.quantity for item in order_items 
                if not condition.item_id or item.item_id == condition.item_id
            )
            return condition.value_from <= total_quantity <= condition.value_to
        
        elif condition_type == 'VALUE_RANGE':
            total_value = sum(
                item.line_total for item in order_items 
                if not condition.item_id or item.item_id == condition.item_id
            ) or Decimal('0')
            return condition.value_from <= total_value <= condition.value_to

        elif condition_type == 'EXACT_QUANTITY':
            total_quantity = sum(
                item.quantity for item in order_items
                if not condition.item_id or item.item_id == condition.item_id
            )
            return total_quantity == condition.value_from
        
        elif condition_type == 'ITEM_COMBO':
            # Check if all required combo items are present in the order
            combo_item_ids = condition.items or []
            if not combo_item_ids and condition.item_id:
                combo_item_ids = [str(condition.item_id)]
            if not combo_item_ids:
                return True
            order_item_ids = {str(item.item_id) for item in order_items}
            return all(str(item_id) in order_item_ids for item_id in combo_item_ids)
        
        return True
    
    def calculate_benefits(self, scheme: Scheme, order: SalesOrder, order_items: Optional[List[SalesOrderItem]] = None) -> Dict[str, Any]:
        """
        Calculate benefits for a scheme on an order.
        
        Args:
            scheme: Scheme instance
            order: SalesOrder instance
            order_items: List of SalesOrderItem instances (optional)
        
        Returns:
            Dict with calculated benefits:
            {
                'total_discount': Decimal,
                'discount_amount': Decimal,
                'free_items': [{'item_id': '...', 'quantity': 5}],
                'benefit_details': [...]
            }
        """
        if order_items is None:
            order_items = list(order.items.all()) if hasattr(order, 'items') else []
        
        total_discount = Decimal('0')
        discount_amount = Decimal('0')
        free_items = []
        benefit_details = []
        
        benefits = scheme.benefits.all()
        
        for benefit in benefits:
            benefit_result = self._calculate_benefit(benefit, order, order_items)
            
            if benefit_result:
                if benefit.benefit_type == 'DISCOUNT_PERCENTAGE':
                    discount_amount += benefit_result.get('amount', Decimal('0'))
                    total_discount += benefit_result.get('percentage', Decimal('0'))
                elif benefit.benefit_type == 'DISCOUNT_AMOUNT':
                    discount_amount += benefit_result.get('amount', Decimal('0'))
                elif benefit.benefit_type == 'FREE_ITEM':
                    free_items.extend(benefit_result.get('items', []))
                elif benefit.benefit_type == 'FREE_QUANTITY':
                    free_items.extend(benefit_result.get('items', []))
                
                benefit_details.append(benefit_result)
        
        return {
            'total_discount': total_discount,
            'discount_amount': discount_amount,
            'free_items': free_items,
            'benefit_details': benefit_details
        }
    
    def _calculate_benefit(self, benefit: SchemeBenefit, order: SalesOrder, order_items: List[SalesOrderItem]) -> Optional[Dict[str, Any]]:
        """
        Calculate a single benefit.
        
        Args:
            benefit: SchemeBenefit instance
            order: SalesOrder instance
            order_items: List of SalesOrderItem instances
        
        Returns:
            Dict with benefit details or None
        """
        benefit_type = benefit.benefit_type
        
        if benefit_type == 'DISCOUNT_PERCENTAGE':
            # Calculate percentage discount
            if benefit.apply_to_all:
                base_amount = sum(item.line_total for item in order_items) or Decimal('0')
            elif benefit.apply_to_item:
                base_amount = sum(
                    item.line_total for item in order_items 
                    if str(item.item_id) == str(benefit.apply_to_item_id)
                ) or Decimal('0')
            elif benefit.apply_to_category:
                base_amount = sum(
                    item.line_total for item in order_items 
                    if str(item.category_id) == str(benefit.apply_to_category_id)
                ) or Decimal('0')
            else:
                return None
            
            # If no eligible items or base amount is 0, return None
            if base_amount <= 0:
                return None
            
            discount_amount = (base_amount * (benefit.discount_value or Decimal('0'))) / Decimal('100')
            return {
                'type': 'DISCOUNT_PERCENTAGE',
                'percentage': benefit.discount_value,
                'amount': discount_amount,
                'base_amount': base_amount
            }
        
        elif benefit_type == 'DISCOUNT_AMOUNT':
            # Fixed amount discount
            if benefit.apply_to_all:
                base_amount = sum(item.line_total for item in order_items) or Decimal('0')
            elif benefit.apply_to_item:
                base_amount = sum(
                    item.line_total for item in order_items
                    if str(item.item_id) == str(benefit.apply_to_item_id)
                ) or Decimal('0')
            elif benefit.apply_to_category:
                base_amount = sum(
                    item.line_total for item in order_items
                    if str(item.category_id) == str(benefit.apply_to_category_id)
                ) or Decimal('0')
            else:
                return None

            # If no eligible items or base amount is 0, return None
            if base_amount <= 0:
                return None

            # Cap discount at base amount to prevent negative totals
            discount_amount = min(benefit.discount_value or Decimal('0'), base_amount)

            return {
                'type': 'DISCOUNT_AMOUNT',
                'amount': discount_amount,
                'base_amount': base_amount
            }
        
        elif benefit_type == 'FREE_ITEM':
            # Free item benefit
            return {
                'type': 'FREE_ITEM',
                'items': [
                    {
                        'item_id': str(benefit.free_item_id),
                        'item_name': benefit.free_item.name if benefit.free_item else '',
                        'quantity': float(benefit.free_quantity) if benefit.free_quantity else 1
                    }
                ]
            }
        
        elif benefit_type == 'FREE_QUANTITY':
            free_qty = float(benefit.free_quantity) if benefit.free_quantity else float(benefit.discount_value or 0)
            if benefit.apply_to_item:
                return {
                    'type': 'FREE_QUANTITY',
                    'items': [{
                        'item_id': str(benefit.apply_to_item_id),
                        'item_name': benefit.apply_to_item.name if benefit.apply_to_item else '',
                        'quantity': free_qty
                    }]
                }
            elif benefit.apply_to_all:
                def _item_name(oi):
                    if hasattr(oi, 'item') and oi.item:
                        return oi.item.name
                    return getattr(oi, 'item_name', '')
                return {
                    'type': 'FREE_QUANTITY',
                    'items': [{
                        'item_id': str(item.item_id),
                        'item_name': _item_name(item),
                        'quantity': free_qty
                    } for item in order_items]
                }
        
        return None
    
    def apply_schemes(self, order: SalesOrder, schemes: List[Scheme], user: Optional[Any] = None) -> Dict[str, Any]:
        """
        Apply multiple schemes to a sales order.
        
        Args:
            order: SalesOrder instance (must be saved)
            schemes: List of Scheme instances to apply
            user: User instance (for audit trail)
        
        Returns:
            Dict with results:
            {
                'applied_schemes': [scheme_ids],
                'total_discount': Decimal,
                'success': bool,
                'message': str
            }
        """
        try:
            order_items = list(order.items.all())
            total_discount = Decimal('0')
            applied_scheme_ids = []
            total_item_scheme_discounts: Dict[str, Decimal] = {item.id: Decimal('0') for item in order_items}
            
            # Clear existing applied schemes
            SalesOrderScheme.objects.filter(sales_order=order).delete()
            SalesOrderItemScheme.objects.filter(
                sales_order_item__order=order
            ).delete()
            
            # Precompute net amounts per item (after manual/item discount)
            item_net_amounts = {}
            for item in order_items:
                qty = Decimal(str(item.quantity or 0))
                rate = Decimal(str(item.rate or 0))
                gross = qty * rate
                if item.discount_type == 'PERCENTAGE':
                    disc = (gross * Decimal(str(item.discount_value or 0))) / Decimal('100')
                else:
                    disc = Decimal(str(item.discount_value or 0))
                net = gross - disc
                item_net_amounts[item.id] = max(net, Decimal('0'))

            for scheme in schemes:
                # Validate conditions
                is_valid, _, _ = self.validate_conditions(scheme, order, order_items)
                
                if not is_valid:
                    self.warnings.append(f"Scheme {scheme.name} conditions not met")
                    continue
                
                # Calculate benefits and allocate to eligible items
                scheme_benefits = self.calculate_benefits(scheme, order, order_items)
                scheme_item_discounts: Dict[str, Decimal] = {}

                for benefit in scheme.benefits.all():
                    benefit_type = benefit.benefit_type

                    if benefit_type not in ['DISCOUNT_PERCENTAGE', 'DISCOUNT_AMOUNT']:
                        continue

                    # Determine eligible items for this benefit
                    if benefit.apply_to_all:
                        eligible_items = list(order_items)
                    elif benefit.apply_to_item:
                        eligible_items = [item for item in order_items if item.item_id == benefit.apply_to_item_id]
                    elif benefit.apply_to_category:
                        eligible_items = [item for item in order_items if item.category_id == benefit.apply_to_category_id]
                    else:
                        eligible_items = []

                    if not eligible_items:
                        continue

                    if benefit_type == 'DISCOUNT_PERCENTAGE':
                        pct = Decimal(str(benefit.discount_value or 0))
                        for item in eligible_items:
                            net = item_net_amounts.get(item.id, Decimal('0'))
                            if net <= 0:
                                continue
                            amount = (net * pct) / Decimal('100')
                            scheme_item_discounts[item.id] = scheme_item_discounts.get(item.id, Decimal('0')) + amount
                    else:  # DISCOUNT_AMOUNT
                        total_net = sum(item_net_amounts.get(item.id, Decimal('0')) for item in eligible_items)
                        if total_net <= 0:
                            continue
                        discount_amount = Decimal(str(benefit.discount_value or 0))
                        if discount_amount > total_net:
                            discount_amount = total_net
                        for item in eligible_items:
                            net = item_net_amounts.get(item.id, Decimal('0'))
                            if net <= 0:
                                continue
                            share = (net / total_net) if total_net > 0 else Decimal('0')
                            amount = discount_amount * share
                            scheme_item_discounts[item.id] = scheme_item_discounts.get(item.id, Decimal('0')) + amount

                scheme_discount_total = sum(scheme_item_discounts.values())
                for item_id, amount in scheme_item_discounts.items():
                    total_item_scheme_discounts[item_id] = total_item_scheme_discounts.get(item_id, Decimal('0')) + amount

                # Create SalesOrderScheme record
                so_scheme, created = SalesOrderScheme.objects.get_or_create(
                    sales_order=order,
                    scheme=scheme,
                    defaults={
                        'scheme_code': scheme.code,
                        'scheme_name': scheme.name,
                        'discount_amount': scheme_discount_total,
                        'free_items': [
                            {k: float(v) if hasattr(v, 'quantize') else v for k, v in fi.items()}
                            for fi in scheme_benefits['free_items']
                        ]
                    }
                )

                total_discount += scheme_discount_total
                applied_scheme_ids.append(str(scheme.id))

                # Apply item-level scheme discounts
                for item in order_items:
                    discount_amount = scheme_item_discounts.get(item.id)
                    if discount_amount and discount_amount > 0:
                        SalesOrderItemScheme.objects.create(
                            sales_order_item=item,
                            scheme=scheme,
                            discount_amount=discount_amount
                        )
            
            # Update item taxable/tax/line totals using scheme discounts
            for item in order_items:
                scheme_disc = total_item_scheme_discounts.get(item.id, Decimal('0'))
                qty = Decimal(str(item.quantity or 0))
                rate = Decimal(str(item.rate or 0))
                gross = qty * rate
                if item.discount_type == 'PERCENTAGE':
                    manual_disc = (gross * Decimal(str(item.discount_value or 0))) / Decimal('100')
                else:
                    manual_disc = Decimal(str(item.discount_value or 0))

                net_after_manual = gross - manual_disc
                net_after_scheme = max(net_after_manual - scheme_disc, Decimal('0'))

                tax_rate = item.get_total_tax_rate()

                if order.tax_type == 'EXCLUSIVE':
                    item.taxable_amount = net_after_scheme
                    item.tax_amount = (net_after_scheme * tax_rate) / Decimal('100')
                    item.line_total = item.taxable_amount + item.tax_amount
                else:
                    item.line_total = net_after_scheme
                    item.taxable_amount = net_after_scheme / (Decimal('1') + tax_rate / Decimal('100')) if tax_rate else net_after_scheme
                    item.tax_amount = item.line_total - item.taxable_amount

                # Reset tax splits
                item.cgst_rate = item.cgst_amount = Decimal('0')
                item.sgst_rate = item.sgst_amount = Decimal('0')
                item.igst_rate = item.igst_amount = Decimal('0')
                item.cess_rate = item.cess_amount = Decimal('0')

                taxable = Decimal(str(item.taxable_amount or 0))
                is_same_state = order.is_same_state()
                compositions = item.item.current_tax_composition if item.item else []

                for comp in compositions:
                    tax = comp.tax
                    rate = Decimal(str(tax.tax_rate))
                    amount = (taxable * rate) / Decimal('100')

                    if comp.composition_type == 'PRIMARY' and tax.tax_type == 'GST':
                        if is_same_state:
                            half_rate = rate / Decimal('2')
                            half_amount = amount / Decimal('2')
                            item.cgst_rate = half_rate
                            item.cgst_amount = half_amount
                            item.sgst_rate = half_rate
                            item.sgst_amount = half_amount
                        else:
                            item.igst_rate = rate
                            item.igst_amount = amount
                    elif comp.composition_type == 'CESS' or tax.is_cess:
                        item.cess_rate = rate
                        item.cess_amount = amount

                SalesOrderItem.objects.filter(id=item.id).update(
                    taxable_amount=item.taxable_amount,
                    tax_amount=item.tax_amount,
                    line_total=item.line_total,
                    cgst_rate=item.cgst_rate,
                    cgst_amount=item.cgst_amount,
                    sgst_rate=item.sgst_rate,
                    sgst_amount=item.sgst_amount,
                    igst_rate=item.igst_rate,
                    igst_amount=item.igst_amount,
                    cess_rate=item.cess_rate,
                    cess_amount=item.cess_amount,
                )

            # Update order totals after item recalculation
            order.calculate_totals()
            
            return {
                'applied_schemes': applied_scheme_ids,
                'total_discount': float(total_discount),
                'success': True,
                'message': f'Applied {len(applied_scheme_ids)} schemes'
            }
        
        except Exception as e:
            self.errors.append(str(e))
            return {
                'applied_schemes': [],
                'total_discount': 0.0,
                'success': False,
                'message': f'Error applying schemes: {str(e)}'
            }
    
    def get_errors(self) -> List[str]:
        """Get list of errors encountered"""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Get list of warnings encountered"""
        return self.warnings
