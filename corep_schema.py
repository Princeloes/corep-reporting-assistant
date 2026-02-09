"""
COREP Template Schema Definitions

This module defines the schema for COREP reporting templates,
including field definitions, data types, and validation rules.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class DataType(Enum):
    """Enumeration of data types for COREP fields."""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    PERCENTAGE = "percentage"


class ValidationRule(Enum):
    """Enumeration of validation rules."""
    REQUIRED = "required"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    LENGTH = "length"
    PATTERN = "pattern"
    CONSISTENCY = "consistency"


@dataclass
class FieldDefinition:
    """Defines a single field in a COREP template."""
    
    field_id: str
    field_name: str
    description: str
    data_type: DataType
    required: bool = False
    validations: List[Dict[str, Any]] = field(default_factory=list)
    regulatory_reference: Optional[str] = None
    instructions: Optional[str] = None
    
    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this field's rules.
        
        Args:
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None or value == "":
            if self.required:
                return False, f"Field {self.field_id} is required"
            return True, None
        
        # Type validation
        if self.data_type == DataType.INTEGER:
            try:
                int(value)
            except (ValueError, TypeError):
                return False, f"Field {self.field_id} must be an integer"
        
        elif self.data_type == DataType.DECIMAL:
            try:
                float(value)
            except (ValueError, TypeError):
                return False, f"Field {self.field_id} must be a decimal number"
        
        elif self.data_type == DataType.PERCENTAGE:
            try:
                pct = float(value)
                if pct < 0 or pct > 100:
                    return False, f"Field {self.field_id} must be between 0 and 100"
            except (ValueError, TypeError):
                return False, f"Field {self.field_id} must be a valid percentage"
        
        elif self.data_type == DataType.DATE:
            from datetime import datetime
            try:
                datetime.fromisoformat(str(value))
            except (ValueError, TypeError):
                return False, f"Field {self.field_id} must be a valid date (ISO format)"
        
        # Custom validation rules
        for validation in self.validations:
            rule_type = validation.get("type")
            
            if rule_type == ValidationRule.MIN_VALUE.value:
                min_val = validation.get("value")
                try:
                    if float(value) < min_val:
                        return False, f"Field {self.field_id} must be >= {min_val}"
                except (ValueError, TypeError):
                    pass
            
            elif rule_type == ValidationRule.MAX_VALUE.value:
                max_val = validation.get("value")
                try:
                    if float(value) > max_val:
                        return False, f"Field {self.field_id} must be <= {max_val}"
                except (ValueError, TypeError):
                    pass
        
        return True, None


@dataclass
class CorepTemplate:
    """Represents a complete COREP reporting template."""
    
    template_id: str
    template_name: str
    description: str
    version: str
    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
    master_rules: List[Dict[str, str]] = field(default_factory=list)
    
    def add_field(self, field_def: FieldDefinition) -> None:
        """Add a field definition to the template."""
        self.fields[field_def.field_id] = field_def
    
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate complete data against template.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        for field_id, field_def in self.fields.items():
            value = data.get(field_id)
            is_valid, error_msg = field_def.validate(value)
            if not is_valid:
                errors.append(error_msg)
        
        return len(errors) == 0, errors


# Define the Own Funds Template (Example)
def create_own_funds_template() -> CorepTemplate:
    """Create the Own Funds COREP template."""
    
    template = CorepTemplate(
        template_id="OF",
        template_name="Own Funds",
        description="COREP Own Funds template for reporting total capital",
        version="1.0",
    )
    
    # Tier 1 Capital
    template.add_field(FieldDefinition(
        field_id="OF_101",
        field_name="Common Equity Tier 1 (CET1) Capital",
        description="Total CET1 capital including share capital and retained earnings",
        data_type=DataType.DECIMAL,
        required=True,
        validations=[
            {"type": ValidationRule.MIN_VALUE.value, "value": 0}
        ],
        regulatory_reference="CRR Article 50",
        instructions="Sum of eligible common equity tier 1 items"
    ))
    
    template.add_field(FieldDefinition(
        field_id="OF_102",
        field_name="Additional Tier 1 (AT1) Capital",
        description="Additional Tier 1 capital instruments",
        data_type=DataType.DECIMAL,
        required=True,
        validations=[
            {"type": ValidationRule.MIN_VALUE.value, "value": 0}
        ],
        regulatory_reference="CRR Article 51",
        instructions="Eligible AT1 instruments meeting CRR criteria"
    ))
    
    template.add_field(FieldDefinition(
        field_id="OF_103",
        field_name="Tier 1 Capital Total",
        description="Total Tier 1 Capital (CET1 + AT1)",
        data_type=DataType.DECIMAL,
        required=True,
        validations=[
            {"type": ValidationRule.MIN_VALUE.value, "value": 0}
        ],
        regulatory_reference="CRR Article 49",
        instructions="Calculated field: OF_101 + OF_102"
    ))
    
    # Tier 2 Capital
    template.add_field(FieldDefinition(
        field_id="OF_201",
        field_name="Tier 2 (T2) Capital",
        description="Tier 2 subordinated capital",
        data_type=DataType.DECIMAL,
        required=True,
        validations=[
            {"type": ValidationRule.MIN_VALUE.value, "value": 0}
        ],
        regulatory_reference="CRR Article 62",
        instructions="Eligible Tier 2 instruments"
    ))
    
    # Total Own Funds
    template.add_field(FieldDefinition(
        field_id="OF_300",
        field_name="Total Own Funds",
        description="Total capital resources of the bank",
        data_type=DataType.DECIMAL,
        required=True,
        validations=[
            {"type": ValidationRule.MIN_VALUE.value, "value": 0}
        ],
        regulatory_reference="CRR Article 48",
        instructions="Calculated field: OF_103 + OF_201"
    ))
    
    template.add_field(FieldDefinition(
        field_id="OF_301",
        field_name="Reporting Date",
        description="Date of the reporting period",
        data_type=DataType.DATE,
        required=True,
        regulatory_reference="COREP ITS",
        instructions="End of quarter date in ISO format (YYYY-MM-DD)"
    ))
    
    # Master Rules
    template.master_rules = [
        {
            "rule_id": "MR_001",
            "description": "Tier 1 Total must equal sum of CET1 and AT1",
            "formula": "OF_103 = OF_101 + OF_102"
        },
        {
            "rule_id": "MR_002",
            "description": "Total Own Funds must equal Tier 1 plus Tier 2",
            "formula": "OF_300 = OF_103 + OF_201"
        },
        {
            "rule_id": "MR_003",
            "description": "All capital amounts must be non-negative",
            "condition": "All capital fields >= 0"
        }
    ]
    
    return template


# Define the Capital Requirements Template (Example)
def create_capital_requirements_template() -> CorepTemplate:
    """Create the Capital Requirements COREP template."""
    
    template = CorepTemplate(
        template_id="CR",
        template_name="Capital Requirements",
        description="COREP Capital Requirements template",
        version="1.0",
    )
    
    template.add_field(FieldDefinition(
        field_id="CR_101",
        field_name="Pillar 1 - Credit Risk",
        description="Capital requirement for credit risk",
        data_type=DataType.DECIMAL,
        required=True,
        validations=[
            {"type": ValidationRule.MIN_VALUE.value, "value": 0}
        ],
        regulatory_reference="CRR Part 3",
        instructions="Capital requirement for all credit exposures"
    ))
    
    template.add_field(FieldDefinition(
        field_id="CR_102",
        field_name="Pillar 1 - Market Risk",
        description="Capital requirement for market risk",
        data_type=DataType.DECIMAL,
        required=True,
        validations=[
            {"type": ValidationRule.MIN_VALUE.value, "value": 0}
        ],
        regulatory_reference="CRR Part 3",
        instructions="Capital requirement for trading book exposures"
    ))
    
    template.add_field(FieldDefinition(
        field_id="CR_103",
        field_name="Pillar 1 - Operational Risk",
        description="Capital requirement for operational risk",
        data_type=DataType.DECIMAL,
        required=True,
        validations=[
            {"type": ValidationRule.MIN_VALUE.value, "value": 0}
        ],
        regulatory_reference="CRR Part 3",
        instructions="Capital requirement for operational risk"
    ))
    
    template.add_field(FieldDefinition(
        field_id="CR_200",
        field_name="Total Pillar 1 Capital Requirement",
        description="Sum of all Pillar 1 requirements",
        data_type=DataType.DECIMAL,
        required=True,
        regulatory_reference="CRR Article 92",
        instructions="Calculated: CR_101 + CR_102 + CR_103"
    ))
    
    return template


# Template Registry
TEMPLATE_REGISTRY = {
    "own_funds": create_own_funds_template(),
    "capital_requirements": create_capital_requirements_template(),
}


def get_template(template_name: str) -> Optional[CorepTemplate]:
    """Retrieve a template by name."""
    return TEMPLATE_REGISTRY.get(template_name.lower())


def list_templates() -> List[str]:
    """List all available templates."""
    return list(TEMPLATE_REGISTRY.keys())
