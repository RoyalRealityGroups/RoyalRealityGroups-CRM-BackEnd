import json

def extract_variables_from_template(template_data):
    try:
        schemas = template_data.get("schemas", [])
        variables = []
        multi_variables = []
        table_variables = []
        svg_variables = []
        image_variables = []

        for page in schemas:
            for field in page:
                if not isinstance(field, dict):
                    continue

                field_name = field.get("name")
                field_type = field.get("type")
                field_content = field.get("content")

                if field_type == "text" and field_name:
                    variables.append(field_name)

                elif field_type == "multiVariableText":
                    field_vars = field.get("variables", [])
                    multi_variables.append({
                        "name": field_name,
                        "variables": field_vars 
                    })

                elif field_type == "table":
                    field_vars = []
                    try:
                        var_array_a = json.loads(field_content)
                        if len(var_array_a) > 0:
                            field_vars.extend(var_array_a[0])
                    except:
                        pass

                    if field_name:
                        table_variables.append({
                            "name": field_name,
                            "variables": field_vars
                        })

                elif field_type == "svg":
                    svg_variables.append(field_name)

                elif field_type == "image":
                    image_variables.append(field_name)

        variables = sorted(set(variables))

        return {
            "variables": variables,
            "multi_variables": multi_variables,
            "table_variables": table_variables,
            "svg_variables": svg_variables,
            "image_variables": image_variables,
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "variables": [],
            "multi_variables": [],
            "table_variables": [],
            "svg_variables": [],
            "image_variables": [],
        }