"""
Custom exception handlers for better error messages
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound, Throttled
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ObjectDoesNotExist
import re
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides user-friendly error messages
    for database constraint violations and other common errors.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    logger.error(f"Exception: {exc}", exc_info=True)
    
    # Handle ProtectedError (foreign key constraint on delete)
    if isinstance(exc, ProtectedError):
        protected_objects = exc.protected_objects
        if protected_objects:
            # Get the model name from the first protected object
            model_name = protected_objects.model._meta.verbose_name_plural if hasattr(protected_objects, 'model') else 'related records'
            count = len(protected_objects) if hasattr(protected_objects, '__len__') else 'some'
            
            return Response(
                {'detail': f'Cannot delete this record because it is being used by {count} {model_name}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {'detail': 'Cannot delete this record because it is being used by other records.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle database integrity errors
    if isinstance(exc, IntegrityError):
        error_message = str(exc)
        user_friendly_message = parse_integrity_error(error_message)
        
        return Response(
            {'detail': user_friendly_message, 'error': 'Integrity Error'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle object not found
    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {'detail': 'The requested resource was not found.', 'error': 'Not Found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Enhance validation errors
    if isinstance(exc, ValidationError) and response:
        # Pass through duplicate-detection responses (Lead, etc.) untouched
        if isinstance(response.data, dict) and response.data.get('has_duplicates'):
            return response

        # Check if it's a simple detail message
        if isinstance(response.data, dict) and 'detail' in response.data and len(response.data) == 1:
            # Return just the detail message for better frontend display
            return Response(
                {'detail': response.data['detail']},
                status=response.status_code
            )
        
        response.data = {
            'detail': 'Validation failed. Please check your input.',
            'errors': response.data,
            'error': 'Validation Error'
        }
    
    # Enhance permission denied errors
    if isinstance(exc, PermissionDenied) and response:
        response.data = {
            'detail': 'You do not have permission to perform this action.',
            'error': 'Permission Denied'
        }
    
    # Enhance not found errors
    if isinstance(exc, NotFound) and response:
        response.data = {
            'detail': 'The requested resource was not found.',
            'error': 'Not Found'
        }
    
    # Enhance throttle errors
    
    # if isinstance(exc, Throttled) and response:
    #     wait_time = exc.wait if hasattr(exc, 'wait') else 60
    #     response.data = {
    #         'detail': f'Too many requests. Please wait {int(wait_time)} seconds and try again.',
    #         'error': 'Rate Limit Exceeded',
    #         'retry_after': int(wait_time)
    #     }
    
    return response


def parse_integrity_error(error_message):
    """
    Parse database integrity error messages and return user-friendly messages.
    """
    error_lower = error_message.lower()
    
    # Handle duplicate key constraint violations
    if 'duplicate key value violates unique constraint' in error_lower:
        # Extract constraint name to determine field
        constraint_match = re.search(r'"([^"]+)"', error_message)
        if constraint_match:
            constraint_name = constraint_match.group(1).lower()
            
            # Map constraint patterns to user-friendly messages
            if '_code_' in constraint_name or constraint_name.endswith('_code_key'):
                return 'This code already exists. Please use a different code.'
            elif '_name_' in constraint_name or constraint_name.endswith('_name_key'):
                return 'This name already exists. Please use a different name.'
            elif '_email_' in constraint_name or constraint_name.endswith('_email_key'):
                return 'This email address already exists. Please use a different email.'
            elif '_phone_' in constraint_name or constraint_name.endswith('_phone_key'):
                return 'This phone number already exists. Please use a different phone number.'
            elif 'country' in constraint_name:
                return 'This country already exists in the system.'
            elif 'state' in constraint_name:
                return 'This state already exists in the system.'
            elif 'city' in constraint_name:
                return 'This city already exists in the system.'
            elif 'company' in constraint_name:
                return 'This company already exists in the system.'
        
        # Generic duplicate message
        return 'This record already exists in the system.'
    
    # Handle foreign key constraint violations
    if 'foreign key constraint' in error_lower or 'violates foreign key' in error_lower:
        if 'delete' in error_lower or 'update' in error_lower:
            return 'Cannot delete this record because it is being used by other records.'
        else:
            return 'Invalid reference. Please select a valid option.'
    
    # Handle not null constraint violations
    if 'not null constraint' in error_lower or 'null value in column' in error_lower:
        # Extract column name if possible
        column_match = re.search(r'column "([^"]+)"', error_message)
        if column_match:
            column_name = column_match.group(1)
            return f'The field "{column_name}" is required and cannot be empty.'
        return 'Required field is missing. Please fill in all required fields.'
    
    # Handle check constraint violations
    if 'check constraint' in error_lower:
        return 'Invalid data provided. Please check your input values.'
    
    # Return original message if no specific pattern matches
    return 'A database error occurred. Please check your input and try again.'