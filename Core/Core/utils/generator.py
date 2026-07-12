import os
import json
import uuid
from django.conf import settings

from Core.Core.utils.converters import generate_pdf_via_node
from Core.Reports.models import PdfTemplate

from Core.Core.utils.formaters import format_print_data
from django.core.files.storage import default_storage


def delete_json_files(*file_paths):
    """
    Deletes the given file paths if they exist.
    """
    for path in file_paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Warning: Failed to delete temp file {path}: {e}")


def create_json_files(template_data, variables_data):
    """
    Creates temporary JSON files for template and variable data.
    Returns the full paths of the created files.
    """
    base_path = os.path.join(settings.MEDIA_ROOT, 'temp', 'pdf')
    os.makedirs(base_path, exist_ok=True)

    # Generate unique file names to avoid overwrite conflicts
    uid = uuid.uuid4().hex
    template_json_path = os.path.join(base_path, f'template_{uid}.json')
    variables_json_path = os.path.join(base_path, f'variables_{uid}.json')
    

    try:
        with open(template_json_path, 'w', encoding='utf-8') as tpl_file:
            json.dump(template_data, tpl_file, ensure_ascii=False, indent=2)

        with open(variables_json_path, 'w', encoding='utf-8') as var_file:
            json.dump(variables_data, var_file, ensure_ascii=False, indent=2)

        return template_json_path, variables_json_path

    except Exception as e:
        # Clean up partially written files
        delete_json_files(template_json_path, variables_json_path)
        raise Exception(f"Failed to write JSON files: {e}")


def get_doc_path(screen, instance_id):
    output_path = None

    template = PdfTemplate.objects.filter(screen=screen, is_active=True).first()
    # print(f"Template found for screen '{screen}': {template}")

    if template:
        template_data = template.template_data
        variables_data = format_print_data(template, instance_id)
        
        template_json_path, variables_json_path = create_json_files(template_data, variables_data)

        output_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'pdf', f'{screen.app_label}{screen.model}_pdf')
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f'{screen.app_label}{screen.model}_{uuid.uuid4().hex}.pdf')

        # print(f"JSON files created: {template_json_path} {variables_json_path} {output_path}")
        try:
            pdf_result_path = generate_pdf_via_node(template_json_path, variables_json_path, output_path)
            output_path = pdf_result_path if pdf_result_path else None
        finally:
            delete_json_files(template_json_path, variables_json_path)


    else:
        print(f"No active template found for screen '{screen}'")

    return output_path


def generate_pdf_weasyprint(html_content):
    """
    Generates a PDF from HTML content using WeasyPrint with better CSS compatibility.
    """
    from weasyprint import HTML
    
    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        print(f"Detailed PDF error: {str(e)}")
        raise Exception(f"PDF generation error: {e}")


def save_pdf_to_media(pdf_content, file_path):
    with default_storage.open(file_path, 'wb') as pdf_file:
        pdf_file.write(pdf_content)

    return file_path