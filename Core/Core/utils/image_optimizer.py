"""Image Optimization Utilities"""
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

def optimize_image(image_field, max_width=1200, max_height=1200, quality=85):
    """
    Optimize uploaded images
    
    Args:
        image_field: Django ImageField
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100)
    
    Returns:
        Optimized InMemoryUploadedFile
    """
    try:
        img = Image.open(image_field)
        
        # Convert RGBA/LA/P to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if needed
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.LANCZOS)
        
        # Save optimized
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Create new file
        filename = image_field.name.split('.')[0] + '.jpg'
        return InMemoryUploadedFile(
            output, 'ImageField', filename,
            'image/jpeg', sys.getsizeof(output), None
        )
    except Exception:
        return image_field
