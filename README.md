# corep-reporting-assistant
LLM-assisted PRA COREP regulatory reporting assistant

# LLM-Assisted PRA COREP Reporting Assistant

## Overview

This is a prototype LLM-assisted regulatory reporting assistant designed to help UK banks subject to PRA regulations prepare accurate COREP (Common European Bank Reporting Format) regulatory returns.

### Problem Addressed

Preparing COREP returns is currently labour-intensive and error-prone because:
- PRA Rulebook and CRR regulations are dense and frequently updated
- Analysts must interpret complex rules and translate them into correct COREP fields
- Manual mapping between regulations and data fields is time-consuming
- Validation and consistency checking requires extensive expertise
- Audit trails for regulatory justification are difficult to maintain

### Solution

This assistant provides:
1. **Automated Rule Retrieval** - Fetches relevant PRA Rulebook and CRR sections based on the reporting question
2. **LLM-Driven Processing** - Uses language models to interpret regulations and extract/calculate required values
3. **Structured Output** - Generates data aligned to predefined COREP template schemas
4. **Template Mapping** - Converts structured output into human-readable COREP report formats
5. **Data Validation** - Validates completeness, consistency, and compliance with master rules
6. **Comprehensive Audit Trail** - Logs which regulations justified each populated field

## Project Structure

```
assisment/
├── src/
│   ├── corep_schema.py         # COREP template definitions and schemas
│   ├── pra_retrieval.py         # Regulatory rule retrieval system
│   ├── llm_processor.py         # LLM interface and processing
│   ├── template_mapper.py       # Template mapping and report generation
│   ├── audit_logger.py          # Comprehensive audit logging
│   └── main.py                  # Main application and orchestrator
├── data/
│   └── (placeholder for sample data/rules)
├── tests/
│   └── test_suite.py            # Comprehensive test suite
└── README.md                    # This file
```

## Core Components

### 1. COREP Schema Module (`corep_schema.py`)

Defines regulatory reporting templates with:
- Field definitions (ID, name, type, validation rules)
- Data types (Integer, Decimal, Boolean, Date, Percentage)
- Template hierarchy (Own Funds, Capital Requirements, etc.)
- Master rules for consistency validation

**Key Classes:**
- `FieldDefinition` - Individual field specification
- `CorepTemplate` - Complete template with all fields and rules
- `DataType`, `ValidationRule` - Enumerations for schema

**Example Templates:**
- **Own Funds** - Reporting capital composition (CET1, AT1, Tier 2)
- **Capital Requirements** - Pillar 1 capital requirements

### 2. PRA Rule Retrieval Module (`pra_retrieval.py`)

Maintains database of PRA Rulebook and CRR regulations with:
- Rule text and regulatory references
- Keyword indexing for fast retrieval
- Source tracking (e.g., CRR Article 50, PRA Rulebook)
- Effective dates and applicability

**Key Classes:**
- `RegulatoryRule` - Individual regulation/guidance
- `PraRuleBook` - Rule database and search functionality

**Search Capabilities:**
- By keyword (e.g., "CET1", "capital")
- By source (e.g., "CRR", "PRA Rulebook")
- By template relevance (e.g., "own_funds")

### 3. LLM Processor Module (`llm_processor.py`)

Interfaces with language models to:
- Construct prompts with regulatory context
- Process natural language questions
- Extract/calculate structured field values
- Generate confidence scores
- Justify outputs with regulatory references

**Key Classes:**
- `ProcessingRequest` - Input request with question, scenario, and rules
- `ProcessingResult` - Output with values, scores, and justifications
- `MockLLMProcessor` - Demonstration processor (no API calls)
- `RealLLMProcessor` - OpenAI API integration (requires API key)

**Processors:**
- Mock processor for development/testing
- Real processor supporting OpenAI GPT-4

### 4. Template Mapper Module (`template_mapper.py`)

Converts structured output to human-readable reports:
- HTML reports with styling and interactivity
- Plain text reports for audit trails
- CSV extracts for spreadsheet import
- Data validation against schema rules
- Missing data detection
- Consistency checking

**Key Classes:**
- `TemplateValidator` - Schema and rule validation
- `CorepReportGenerator` - Multi-format report creation
- `MissingDataDetector` - Data quality analysis

### 5. Audit Logger Module (`audit_logger.py`)

Maintains comprehensive audit trail of:
- All field updates with timestamps and users
- Field value history and change tracking
- Rule usage statistics
- Validation results and dates
- Complete audit reports

**Key Classes:**
- `AuditLogEntry` - Single logged action
- `ValidationEntry` - Validation test results
- `AuditLog` - Complete audit trail management

## Workflow

### Step 1: User Input
User provides:
- Natural language question about the reporting requirement
- Reporting scenario with available data

### Step 2: Rule Retrieval
System retrieves relevant regulations:
- Searches PRA Rulebook and CRR
- Returns applicable sections and guidance
- Logs retrieved rules to audit trail

### Step 3: LLM Processing
LLM processor:
- Constructs prompt with regulatory context
- Interprets requirements
- Maps scenario data to template fields
- Generates structured output with confidence scores
- Justifies each field with supporting rules

### Step 4: Data Validation
Validator:
- Checks all required fields are populated
- Validates data types and ranges
- Confirms master rule consistency
- Detects missing or inconsistent data

### Step 5: Report Generation
System generates:
- HTML report with styling
- Plain text audit trail
- CSV extract for systems integration
- Detailed justifications
- Audit log with regulatory references

## Usage Examples

### Basic Python Usage

```python
from main import CorepReportingAssistant

# Create assistant
assistant = CorepReportingAssistant(
    report_name="Own Funds Q4 2024",
    template_id="own_funds"
)

# Define reporting scenario
scenario = {
    "bank_name": "Example Bank plc",
    "reporting_date": "2024-12-31",
    "CET1_capital": 1500.0,
    "AT1_capital": 300.0,
    "Tier2_capital": 250.0,
}

# Ask question
question = "What is our total own funds?"

# Process
result = assistant.process_question(question, scenario)

# Generate report
html_report = assistant.generate_report("html")
text_report = assistant.generate_report("text")

# Export audit trail
assistant.export_audit_log("audit_log.json")
```

### Running the Example

```bash
cd src
python main.py
```

This runs a complete example scenario and generates:
- `report.html` - Formatted COREP report
- `report.txt` - Audit trail
- `report.csv` - Data extract
- `audit_log.json` - Complete audit log

## API Reference

### CorepReportingAssistant

Main orchestrator class.

**Methods:**
- `process_question(question, scenario)` - Process a reporting request
- `generate_report(output_format)` - Generate report (html/text/csv)
- `export_audit_log(filepath)` - Save audit log to JSON
- `get_audit_summary()` - Get summary of audit trail

### PraRuleBook

Rule retrieval and search.

**Methods:**
- `search_by_keyword(keyword)` - Find rules by keyword
- `search_by_source(source)` - Find rules by regulation source
- `get_rule(rule_id)` - Get specific rule
- `get_rules_for_template(template_id)` - Get rules for a template

### TemplateValidator

Schema validation.

**Methods:**
- `validate_data(data)` - Validate fields against template

### CorepReportGenerator

Report generation.

**Methods:**
- `generate_html_report(data, confidence_scores, justifications)`
- `generate_text_report(data, confidence_scores, justifications)`
- `generate_csv_extract(data)`

### AuditLog

Audit trail management.

**Methods:**
- `log(action, field_id, old_value, new_value, regulatory_reference)`
- `log_field_update(field_id, old_value, new_value, regulatory_references)`
- `get_field_history(field_id)` - Get complete history of a field
- `get_rules_used()` - Get statistics on rule usage
- `export_to_file(filepath)` - Save to JSON

## Configuration

### Using OpenAI API (Optional)

To use real LLM processing instead of mock:

```python
import os
os.environ['OPENAI_API_KEY'] = 'your-api-key'

assistant = CorepReportingAssistant(
    report_name="Own Funds Q4 2024",
    template_id="own_funds",
    use_real_llm=True  # Enable real LLM
)
```

### Adding Custom Templates

```python
from corep_schema import CorepTemplate, FieldDefinition, DataType

template = CorepTemplate(
    template_id="custom",
    template_name="My Custom Template",
    description="Custom reporting template",
    version="1.0"
)

template.add_field(FieldDefinition(
    field_id="CUSTOM_001",
    field_name="My Field",
    description="Field description",
    data_type=DataType.DECIMAL,
    required=True
))

# Register template
from corep_schema import TEMPLATE_REGISTRY
TEMPLATE_REGISTRY["custom"] = template
```

### Adding Regulatory Rules

```python
from pra_retrieval import RegulatoryRule, get_rulebook

rulebook = get_rulebook()

rule = RegulatoryRule(
    rule_id="CUSTOM_RULE_1",
    section="My Section",
    title="My Rule Title",
    content="Rule content...",
    source="My Regulation",
    relevance_keywords=["keyword1", "keyword2"]
)

rulebook.add_rule(rule)
```

## Testing

Run the test suite:

```bash
cd tests
python test_suite.py
```

Tests cover:
- Schema validation
- Rule retrieval
- LLM processing
- Template validation
- Report generation
- Audit logging
- Data quality checks

## Key Features

### ✓ End-to-End Workflow
From user question → rule retrieval → LLM processing → validated template → human-readable report

### ✓ Regulatory Compliance
- References specific regulatory articles (CRR, PRA Rulebook)
- Validates against published COREP templates
- Maintains audit trail of all decisions

### ✓ Data Quality
- Validates completeness of required fields
- Checks consistency against master rules
- Detects missing or inconsistent data

### ✓ Audit Trail
- Logs which regulations were used for each field
- Tracks all updates and changes
- Provides compliance evidence

### ✓ Flexible Output
- HTML reports with styling
- Plain text for audit trails
- CSV for system integration
- JSON audit logs

### ✓ Extensible Design
- Easy to add new templates
- Simple to extend rule database
- Pluggable LLM processors

## Limitations and Future Enhancements

### Current Limitations
1. Mock processor used for demonstration (API integration available)
2. Sample regulatory rules provided as examples
3. Two template examples (Own Funds, Capital Requirements)
4. Basic master rule validation

### Future Enhancements
1. Integration with full PRA Rulebook database
2. More COREP template coverage
3. Advanced consistency checking and auto-correction
4. Integration with bank data systems
5. Real-time regulatory updates
6. Multi-bank consolidation reporting
7. Regulatory change impact analysis
8. Advanced confidence scoring with uncertainty quantification

## Supporting Documentation

- **COREP ITS 680/2014** - EBA Implementing Technical Standard on Supervisory Reporting
- **CRR** - Capital Requirements Regulation (EU) 575/2013
- **PRA Rulebook** - UK Prudential Regulation Authority rules
- **EBA Guidelines** - European Banking Authority guidance on regulatory reporting

## Requirements

- Python 3.8+
- OpenAI Python library (optional, for real LLM)

## Installation

```bash
# Clone or download repository
cd assisment

# Install dependencies (optional)
pip install openai  # For real LLM support
```

## License

This is a prototype developed for educational and regulatory compliance purposes.

## Support

For questions or issues:
1. Check the test suite for usage examples
2. Review docstrings in source files
3. Examine the generated reports and audit logs
4. Refer to regulatory documentation included in rule retrieval system

---

**Version:** 1.0 (Prototype)  
**Last Updated:** February 2026  
**Status:** Demonstration/Educational
