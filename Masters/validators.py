import re
from django.core.exceptions import ValidationError
from django.db import models

CONTACT_PHONE_PATTERN = r'^[+]?[0-9]{1,4}?[-\s]?[(]?[0-9]{1,4}[)]?[-\s]?[0-9]{1,4}[-\s]?[0-9]{1,9}$'
CONTACT_EMAIL_PATTERN = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'


def validate_gst_number(value):
    """Validate GST number format"""
    if not value:
        return
    
    # GST format: 2 digits state code + 10 chars PAN + 1 digit entity number + 1 char Z + 1 check digit
    gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
    
    if not re.match(gst_pattern, value.upper()):
        raise ValidationError('Invalid GST number format')


def validate_unique_name_case_insensitive(model_class, name, instance=None, exclude_deleted=True):
    """
    Validate that name is unique (case-insensitive) across non-deleted records
    
    Args:
        model_class: The model class to check against
        name: The name value to validate
        instance: Current instance (for updates)
        exclude_deleted: Whether to exclude deleted records from check
    
    Returns:
        str: Cleaned name (stripped and title cased)
    
    Raises:
        ValidationError: If duplicate found
    """
    if not name:
        return name
    
    # Clean the name
    cleaned_name = name.strip()
    
    # Build queryset for duplicate check
    queryset = model_class.objects.filter(name__iexact=cleaned_name)
    
    # Exclude deleted records if specified
    if exclude_deleted and hasattr(model_class, 'is_deleted'):
        queryset = queryset.filter(is_deleted=False)
    
    # Exclude current instance if updating
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    # Check for duplicates
    if queryset.exists():
        existing = queryset.first()
        raise ValidationError(
            f"A {model_class._meta.verbose_name} with name '{existing.name}' already exists. "
            f"Names are case-insensitive."
        )
    
    return cleaned_name


def validate_unique_code_case_insensitive(model_class, code, instance=None, exclude_deleted=True):
    """
    Validate that code is unique (case-insensitive) across non-deleted records
    
    Args:
        model_class: The model class to check against
        code: The code value to validate
        instance: Current instance (for updates)
        exclude_deleted: Whether to exclude deleted records from check
    
    Returns:
        str: Cleaned code (stripped and uppercased)
    
    Raises:
        ValidationError: If duplicate found
    """
    if not code:
        return code
    
    # Clean the code
    cleaned_code = code.strip().upper()
    
    # Build queryset for duplicate check
    queryset = model_class.objects.filter(code__iexact=cleaned_code)
    
    # Exclude deleted records if specified
    if exclude_deleted and hasattr(model_class, 'is_deleted'):
        queryset = queryset.filter(is_deleted=False)
    
    # Exclude current instance if updating
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    # Check for duplicates
    if queryset.exists():
        existing = queryset.first()
        raise ValidationError(
            f"A {model_class._meta.verbose_name} with code '{existing.code}' already exists. "
            f"Codes are case-insensitive."
        )
    
    return cleaned_code


def add_deleted_prefix_to_field(instance, field_name, prefix="DEL"):
    """
    Add deleted prefix to a field value when record is soft deleted
    
    Args:
        instance: Model instance being deleted
        field_name: Name of the field to modify
        prefix: Prefix to add (default: "DEL")
    
    Returns:
        str: Modified field value with prefix and timestamp
    """
    from datetime import datetime
    
    current_value = getattr(instance, field_name, '')
    if not current_value:
        return current_value
    
    # Check if already has deleted prefix
    if current_value.startswith(f"{prefix}_"):
        return current_value
    
    # Add timestamp to make it unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}_{current_value}"


def restore_field_from_deleted_prefix(instance, field_name, prefix="DEL"):
    """
    Remove deleted prefix from a field value when record is restored
    
    Args:
        instance: Model instance being restored
        field_name: Name of the field to modify
        prefix: Prefix to remove (default: "DEL")
    
    Returns:
        str: Original field value without prefix
    """
    current_value = getattr(instance, field_name, '')
    if not current_value:
        return current_value
    
    # Check if has deleted prefix
    if current_value.startswith(f"{prefix}_"):
        # Remove prefix and timestamp: DEL_20241201_120000_OriginalValue -> OriginalValue
        parts = current_value.split('_', 3)
        if len(parts) >= 4:
            return parts[3]  # Return original value
        elif len(parts) == 3:
            return parts[2]  # Fallback if no timestamp
    
    return current_value


class DuplicateValidationMixin:
    """
    Mixin to add duplicate validation for name and code fields
    """
    
    def clean(self):
        """Override clean method to add validation"""
        super().clean()
        
        # Validate name uniqueness (case-insensitive)
        if hasattr(self, 'name') and self.name:
            self.name = validate_unique_name_case_insensitive(
                self.__class__, 
                self.name, 
                instance=self
            )
        
        # Validate code uniqueness (case-insensitive) - only if not auto-generated
        if hasattr(self, 'code') and self.code and not self._state.adding:
            self.code = validate_unique_code_case_insensitive(
                self.__class__, 
                self.code, 
                instance=self
            )
    
    def delete(self, using=None, keep_parents=False):
        """Override delete to handle soft deletion with prefixes"""
        if hasattr(self, 'is_deleted'):
            # Soft delete - add prefixes to name and code
            if hasattr(self, 'name') and self.name:
                self.name = add_deleted_prefix_to_field(self, 'name')
            
            if hasattr(self, 'code') and self.code:
                self.code = add_deleted_prefix_to_field(self, 'code')
            
            self.is_deleted = True
            self.save(update_fields=['name', 'code', 'is_deleted'] if hasattr(self, 'code') else ['name', 'is_deleted'])
        else:
            # Hard delete
            super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restore a soft-deleted record"""
        if hasattr(self, 'is_deleted') and self.is_deleted:
            # Remove prefixes from name and code
            if hasattr(self, 'name') and self.name:
                self.name = restore_field_from_deleted_prefix(self, 'name')
            
            if hasattr(self, 'code') and self.code:
                self.code = restore_field_from_deleted_prefix(self, 'code')
            
            self.is_deleted = False
            self.save(update_fields=['name', 'code', 'is_deleted'] if hasattr(self, 'code') else ['name', 'is_deleted'])


def validate_pan_number(value):
    """Validate PAN number format"""
    if not value:
        return
    
    # PAN format: 5 letters + 4 digits + 1 letter
    pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    
    if not re.match(pan_pattern, value.upper()):
        raise ValidationError('Invalid PAN number format. Format should be: ABCDE1234F')


def validate_phone_number(value):
    """Validate phone number format"""
    if not value:
        return
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', value)
    
    # Check if it's a valid Indian mobile number (10 digits starting with 6-9)
    if len(digits_only) == 10 and digits_only[0] in '6789':
        return
    
    # Check if it's a valid Indian mobile number with country code (+91)
    if len(digits_only) == 12 and digits_only.startswith('91') and digits_only[2] in '6789':
        return
    
    raise ValidationError('Invalid phone number. Please enter a valid Indian mobile number.')


def validate_contact_phone(value, min_length=10, max_length=15):
    """
    Validate generic contact phone number (mobile/landline with separators).
    Returns trimmed phone string when valid.
    """
    if not value:
        return value

    phone = value.strip()

    if len(phone) < min_length:
        raise ValidationError(f'Phone number must be at least {min_length} digits')
    if len(phone) > max_length:
        raise ValidationError(f'Phone number cannot exceed {max_length} characters')
    if not re.match(CONTACT_PHONE_PATTERN, phone):
        raise ValidationError(
            'Please enter a valid phone number (e.g., +91 9876543210 or 040-12345678)'
        )
    return phone


def validate_contact_email(value):
    """
    Validate generic email format and return trimmed email.
    """
    if not value:
        return value

    email = value.strip()
    if not re.match(CONTACT_EMAIL_PATTERN, email, re.IGNORECASE):
        raise ValidationError(
            'Please enter a valid email address (e.g., john@company.com)'
        )
    return email


def validate_pincode(value):
    """Validate Indian PIN code format"""
    if not value:
        return
    
    # PIN code should be 6 digits
    if not re.match(r'^\d{6}$', value):
        raise ValidationError('Invalid PIN code. PIN code should be 6 digits.')


def validate_email_domain(value):
    """Validate email domain (optional custom validation)"""
    if not value:
        return
    
    # Add any custom email domain validation if needed
    # For now, just basic format check is handled by EmailField
    pass
