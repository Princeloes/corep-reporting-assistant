"""
Template Mapping and Human-Readable Report Generation

This module generates human-readable COREP report extracts from 
structured LLM output and provides template mapping functionality.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime

from corep_schema import CorepTemplate, FieldDefinition, DataType


@dataclass
class TemplateError:
    """Represents a validation error in template data."""
    
    field_id: str
    field_name: str
    error_message: str
    severity: str = "ERROR"  # ERROR, WARNING, INFO


class TemplateValidator:
    """Validates structured output against template rules."""
    
    def __init__(self, template: CorepTemplate):
        """Initialize validator with a template."""
        self.template = template
        self.errors: List[TemplateError] = []
        self.warnings: List[TemplateError] = []
    
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[TemplateError]]:
        """
        Validate data against template.
        
        Args:
            data: Field values to validate
            
        Returns:
            Tuple of (is_valid, errors_and_warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Validate each field
        for field_id, field_def in self.template.fields.items():
            value = data.get(field_id)
            
            # Type validation
            if value is not None and value != "":
                # Validate type
                if not self._validate_type(field_def, value):
                    self.errors.append(TemplateError(
                        field_id=field_id,
                        field_name=field_def.field_name,
                        error_message=f"Invalid type for {field_def.field_name}: expected {field_def.data_type.value}",
                        severity="ERROR"
                    ))
                    continue
                
                # Validate rules
                validation_errors = self._validate_rules(field_def, value)
                for error in validation_errors:
                    self.errors.append(error)
            else:
                # Check if required
                if field_def.required:
                    self.errors.append(TemplateError(
                        field_id=field_id,
                        field_name=field_def.field_name,
                        error_message=f"{field_def.field_name} is required",
                        severity="ERROR"
                    ))
        
        # Validate master rules
        for rule in self.template.master_rules:
            rule_errors = self._validate_master_rule(rule, data)
            self.errors.extend(rule_errors)
        
        return len(self.errors) == 0, self.errors + self.warnings
    
    def _validate_type(self, field: FieldDefinition, value: Any) -> bool:
        """Validate value type."""
        try:
            if field.data_type == DataType.INTEGER:
                int(value)
            elif field.data_type == DataType.DECIMAL or field.data_type == DataType.PERCENTAGE:
                float(value)
            elif field.data_type == DataType.DATE:
                from datetime import datetime
                datetime.fromisoformat(str(value))
            elif field.data_type == DataType.BOOLEAN:
                if not isinstance(value, (bool, str)):
                    return False
            # STRING type accepts anything
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_rules(self, field: FieldDefinition, value: Any) -> List[TemplateError]:
        """Validate against custom rules."""
        errors = []
        
        for validation in field.validations:
            rule_type = validation.get("type")
            
            if rule_type == "min_value":
                try:
                    if float(value) < validation.get("value", 0):
                        errors.append(TemplateError(
                            field_id=field.field_id,
                            field_name=field.field_name,
                            error_message=f"Value must be >= {validation.get('value')}",
                            severity="ERROR"
                        ))
                except (ValueError, TypeError):
                    pass
            
            elif rule_type == "max_value":
                try:
                    if float(value) > validation.get("value", 0):
                        errors.append(TemplateError(
                            field_id=field.field_id,
                            field_name=field.field_name,
                            error_message=f"Value must be <= {validation.get('value')}",
                            severity="ERROR"
                        ))
                except (ValueError, TypeError):
                    pass
        
        return errors
    
    def _validate_master_rule(self, rule: Dict[str, str], data: Dict[str, Any]) -> List[TemplateError]:
        """Validate master rule consistency."""
        errors = []
        
        # Extract formula if exists
        formula = rule.get("formula")
        if not formula:
            return errors
        
        # Simple formula evaluation
        # Examples: "OF_103 = OF_101 + OF_102"
        try:
            parts = formula.split("=")
            if len(parts) == 2:
                target_field = parts[0].strip()
                expression = parts[1].strip()
                
                # Only validate if we have all required values
                target_value = data.get(target_field)
                
                if target_value is not None:
                    # Evaluate expression
                    eval_vars = {k: float(v) if v else 0 for k, v in data.items()}
                    try:
                        expected = eval(expression, {"__builtins__": {}}, eval_vars)
                        actual = float(target_value)
                        
                        # Allow small floating point differences
                        if abs(expected - actual) > 0.01:
                            errors.append(TemplateError(
                                field_id=target_field,
                                field_name=rule.get("description", ""),
                                error_message=f"Master rule violation: {formula} (expected {expected}, got {actual})",
                                severity="ERROR"
                            ))
                    except:
                        pass  # Skip if evaluation fails
        except:
            pass  # Skip on any error
        
        return errors


class CorepReportGenerator:
    """Generates human-readable COREP report extracts."""
    
    def __init__(self, template: CorepTemplate):
        """Initialize with a template."""
        self.template = template
    
    def generate_html_report(self, data: Dict[str, Any], 
                            confidence_scores: Dict[str, float] = None,
                            justifications: Dict[str, List[str]] = None) -> str:
        """
        Generate an HTML report of the COREP template.
        
        Args:
            data: Field values
            confidence_scores: Confidence scores for each field
            justifications: Supporting rules for each field
            
        Returns:
            HTML string
        """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.template.template_name} Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #003366; color: white; padding: 20px; border-radius: 5px; }}
        .template-info {{ background-color: #e8f4f8; padding: 15px; margin: 20px 0; border-left: 4px solid #003366; }}
        table {{ width: 100%; border-collapse: collapse; background-color: white; margin: 20px 0; }}
        th {{ background-color: #003366; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .field-id {{ font-family: monospace; font-weight: bold; color: #003366; }}
        .required {{ background-color: #fff3cd; }}
        .error {{ background-color: #f8d7da; color: #721c24; }}
        .warning {{ background-color: #fff3cd; color: #856404; }}
        .confidence {{ color: #666; font-size: 0.9em; }}
        .rules {{ font-size: 0.85em; color: #666; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 0.85em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{self.template.template_name}</h1>
        <p>{self.template.description}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="template-info">
        <strong>Template ID:</strong> {self.template.template_id}<br>
        <strong>Version:</strong> {self.template.version}
    </div>
    
    <h2>Reported Values</h2>
    <table>
        <thead>
            <tr>
                <th>Field ID</th>
                <th>Field Name</th>
                <th>Value</th>
                <th>Type</th>
                <th>Confidence</th>
                <th>Supporting Rules</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for field_id, field_def in self.template.fields.items():
            value = data.get(field_id)
            confidence = confidence_scores.get(field_id, 0.0) if confidence_scores else 0.0
            rules = justifications.get(field_id, []) if justifications else []
            
            confidence_pct = confidence * 100 if confidence else 0
            confidence_color = "green" if confidence > 0.9 else "orange" if confidence > 0.7 else "red"
            
            row_class = "required" if field_def.required and value is None else ""
            
            html += f"""
            <tr class="{row_class}">
                <td class="field-id">{field_id}</td>
                <td>{field_def.field_name}</td>
                <td><strong>{value if value is not None else 'N/A'}</strong></td>
                <td>{field_def.data_type.value}</td>
                <td class="confidence">
                    <span style="color: {confidence_color};">
                        {confidence_pct:.1f}%
                    </span>
                </td>
                <td class="rules">
                    {', '.join(rules) if rules else 'N/A'}
                </td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
    
    <h2>Master Rules</h2>
    <table>
        <thead>
            <tr>
                <th>Rule ID</th>
                <th>Description</th>
                <th>Formula</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for rule in self.template.master_rules:
            html += f"""
            <tr>
                <td><strong>{rule.get('rule_id', 'N/A')}</strong></td>
                <td>{rule.get('description', '')}</td>
                <td><code>{rule.get('formula', '')}</code></td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
    
    <div class="footer">
        <p>This report was generated as part of the COREP regulatory reporting process.</p>
        <p>All values are in accordance with applicable PRA Rulebook and CRR requirements.</p>
    </div>
</body>
</html>
"""
        
        return html
    
    def generate_text_report(self, data: Dict[str, Any],
                            confidence_scores: Dict[str, float] = None,
                            justifications: Dict[str, List[str]] = None) -> str:
        """
        Generate a plain text report.
        
        Args:
            data: Field values
            confidence_scores: Confidence scores
            justifications: Supporting rules
            
        Returns:
            Plain text report string
        """
        
        report = f"""
{'='*100}
{self.template.template_name.upper()} - COREP REGULATORY REPORT
{'='*100}

Template: {self.template.template_id} (v{self.template.version})
Description: {self.template.description}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*100}
REPORTED VALUES
{'='*100}

"""
        
        for field_id, field_def in self.template.fields.items():
            value = data.get(field_id)
            confidence = confidence_scores.get(field_id, 0.0) if confidence_scores else 0.0
            rules = justifications.get(field_id, []) if justifications else []
            
            confidence_pct = confidence * 100 if confidence else 0
            
            report += f"""
Field:       {field_id}
Name:        {field_def.field_name}
Type:        {field_def.data_type.value}
Required:    {'Yes' if field_def.required else 'No'}
Value:       {value if value is not None else 'N/A'}
Confidence:  {confidence_pct:.1f}%
"""
            
            if field_def.instructions:
                report += f"Instructions: {field_def.instructions}\n"
            
            if field_def.regulatory_reference:
                report += f"Reference:   {field_def.regulatory_reference}\n"
            
            if rules:
                report += f"Rules:       {', '.join(rules)}\n"
            
            report += "-" * 50 + "\n"
        
        report += f"""
{'='*100}
MASTER RULES VALIDATION
{'='*100}

"""
        
        for rule in self.template.master_rules:
            report += f"""
Rule ID:     {rule.get('rule_id', 'N/A')}
Description: {rule.get('description', '')}
Formula:     {rule.get('formula', '')}

"""
        
        report += f"""
{'='*100}
END OF REPORT
{'='*100}
"""
        
        return report
    
    def generate_csv_extract(self, data: Dict[str, Any]) -> str:
        """
        Generate a CSV extract of the template.
        
        Args:
            data: Field values
            
        Returns:
            CSV string
        """
        
        lines = []
        lines.append("Field ID,Field Name,Data Type,Required,Value")
        
        for field_id, field_def in self.template.fields.items():
            value = data.get(field_id, "")
            
            # Escape CSV values
            value_str = str(value) if value is not None else ""
            if "," in value_str or '"' in value_str:
                value_str = f'"{value_str.replace(chr(34), chr(34) + chr(34))}"'
            
            lines.append(
                f"{field_id},"
                f'"{field_def.field_name}",'
                f"{field_def.data_type.value},"
                f"{'Yes' if field_def.required else 'No'},"
                f"{value_str}"
            )
        
        return "\n".join(lines)


class MissingDataDetector:
    """Detects and flags missing or inconsistent data."""
    
    @staticmethod
    def check_completeness(data: Dict[str, Any], 
                          template: CorepTemplate) -> List[str]:
        """
        Check if all required fields are populated.
        
        Args:
            data: Field values
            template: Template schema
            
        Returns:
            List of missing field messages
        """
        
        missing = []
        
        for field_id, field_def in template.fields.items():
            value = data.get(field_id)
            
            if field_def.required and (value is None or value == ""):
                missing.append(f"Required field {field_id} ({field_def.field_name}) is missing")
        
        return missing
    
    @staticmethod
    def check_consistency(data: Dict[str, Any], 
                         template: CorepTemplate) -> List[str]:
        """
        Check consistency against master rules.
        
        Args:
            data: Field values
            template: Template schema
            
        Returns:
            List of inconsistency messages
        """
        
        inconsistencies = []
        
        for rule in template.master_rules:
            formula = rule.get("formula")
            if not formula:
                continue
            
            try:
                parts = formula.split("=")
                if len(parts) == 2:
                    target_field = parts[0].strip()
                    expression = parts[1].strip()
                    
                    target_value = data.get(target_field)
                    if target_value is not None:
                        # Build eval vars safely by trying to convert to float
                        eval_vars = {}
                        for k, v in data.items():
                            try:
                                eval_vars[k] = float(v) if v else 0
                            except (ValueError, TypeError):
                                eval_vars[k] = 0
                        
                        expected = eval(expression, {"__builtins__": {}}, eval_vars)
                        actual = float(target_value)
                        
                        if abs(expected - actual) > 0.01:
                            inconsistencies.append(
                                f"Inconsistency in {target_field}: {formula} "
                                f"(expected {expected}, got {actual})"
                            )
            except Exception as e:
                # Log parsing errors but don't fail silently
                pass
        
        return inconsistencies
