from django.db.models import Q


def apply_company_location_filter(queryset, user, company_field='company', location_field=None):
    """
    Filter queryset based on user's company and location access.

    Cases:
    1. Superuser: No filtering - all data displayed
    2. has_all_companies + has_all_locations: No filtering
    3. has_all_companies + specific locations: Filter by user's assigned locations
    4. specific companies + has_all_locations: Filter by user's assigned companies
    5. specific companies + specific locations: Filter by both companies and locations

    Args:
        queryset: The Django queryset to filter
        user: The authenticated user
        company_field: Name of the company FK field on the model (supports lookup paths like 'invoice__company')
        location_field: Name of the location FK field on the model (or None if model has no location field)

    Returns:
        Filtered queryset
    """
    if not getattr(user, 'is_authenticated', False):
        return queryset.none()

    # Case 1: Superuser sees everything
    if getattr(user, 'is_superuser', False):
        return queryset

    # Case 2: All companies + all locations = no filtering needed
    has_all_companies = getattr(user, 'has_all_companies', False)
    has_all_locations = getattr(user, 'has_all_locations', False)
    
    # If location_field is None, ignore location checks
    if location_field is None:
        if has_all_companies:
            return queryset
    else:
        if has_all_companies and has_all_locations:
            return queryset

    filters = Q()

    # Cases 4 & 5: Specific companies
    if not has_all_companies and company_field:
        company_manager = getattr(user, 'companies', None)
        company_ids = list(company_manager.values_list('id', flat=True)) if company_manager is not None else []
        filters &= Q(**{f'{company_field}__in': company_ids})

    # Cases 3 & 5: Specific locations
    if not has_all_locations and location_field:
        location_manager = getattr(user, 'locations', None)
        location_ids = list(location_manager.values_list('id', flat=True)) if location_manager is not None else []
        filters &= Q(**{f'{location_field}__in': location_ids})

    return queryset.filter(filters)


def apply_channel_partner_company_location_filter(
    queryset,
    user,
    company_field='company',
    state_field='state',
    city_field='city',
    coverage_relation='locations'
):
    """
    Filter channel partner querysets by user's company and location access.

    Location filtering uses both:
    1. Direct partner address fields (`state`/`city`)
    2. Coverage mappings (`locations__state`/`locations__city`) when available
    
    Note: For channel partner users (DISTRIBUTOR, SUPERSTOCKIST, RETAILER),
    location filtering is skipped as they should see their assigned partners
    regardless of location settings.
    """
    queryset = apply_company_location_filter(
        queryset,
        user,
        company_field=company_field,
        location_field=None
    )

    if not getattr(user, 'is_authenticated', False):
        return queryset.none()

    if getattr(user, 'is_superuser', False) or getattr(user, 'has_all_locations', False):
        return queryset
    
    # Skip location filtering for channel partner users
    # They should see their assigned partners regardless of location settings
    channel_partner_type = getattr(user, 'channel_partner_type', 'STAFF')
    if channel_partner_type in ['SUPERSTOCKIST', 'DISTRIBUTOR', 'RETAILER']:
        return queryset

    location_manager = getattr(user, 'locations', None)
    if location_manager is None:
        return queryset.none()

    state_ids = list(location_manager.values_list('state_id', flat=True).distinct())
    city_ids = list(location_manager.values_list('city_id', flat=True).distinct())

    if not state_ids and not city_ids:
        return queryset.none()

    location_filters = Q()

    if state_field and state_ids:
        location_filters |= Q(**{f'{state_field}_id__in': state_ids})
    if city_field and city_ids:
        location_filters |= Q(**{f'{city_field}_id__in': city_ids})

    if coverage_relation:
        if state_ids:
            location_filters |= Q(**{f'{coverage_relation}__state_id__in': state_ids})
        if city_ids:
            location_filters |= Q(**{f'{coverage_relation}__city_id__in': city_ids})

    return queryset.filter(location_filters)


def apply_company_location_filter_for_users(queryset, user):
    """
    Filter User queryset based on current user's company and location access.
    Shows users who share at least one company/location with the current user.

    Args:
        queryset: User queryset to filter
        user: The authenticated user

    Returns:
        Filtered queryset
    """
    if not getattr(user, 'is_authenticated', False):
        return queryset.none()

    # Superuser sees everything
    if getattr(user, 'is_superuser', False):
        return queryset

    # All companies + all locations = no filtering needed
    has_all_companies = getattr(user, 'has_all_companies', False)
    has_all_locations = getattr(user, 'has_all_locations', False)
    if has_all_companies and has_all_locations:
        return queryset

    filters = Q()

    # Specific companies: show users who share at least one company or have all_companies access
    # Only filter by companies if the model has a companies field
    has_companies_field = False
    try:
        queryset.model._meta.get_field('companies')
        has_companies_field = True
    except Exception:
        pass

    if not has_all_companies and has_companies_field:
        company_manager = getattr(user, 'companies', None)
        company_ids = list(company_manager.values_list('id', flat=True)) if company_manager is not None else []
        filters &= (Q(companies__id__in=company_ids) | Q(has_all_companies=True))

    # Specific locations: show users who share at least one location or have all_locations access
    # Only filter by locations if the model has a locations field
    has_locations_field = False
    try:
        queryset.model._meta.get_field('locations')
        has_locations_field = True
    except Exception:
        pass

    if not has_all_locations and has_locations_field:
        location_manager = getattr(user, 'locations', None)
        location_ids = list(location_manager.values_list('id', flat=True)) if location_manager is not None else []
        filters &= (Q(locations__id__in=location_ids) | Q(has_all_locations=True))

    if filters:
        return queryset.filter(filters).distinct()
    return queryset
