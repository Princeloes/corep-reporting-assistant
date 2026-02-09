"""
Quick Start Guide

This document provides a quick start guide to using the 
LLM-assisted COREP Reporting Assistant.
"""

# QUICK START GUIDE

## Installation

1. Ensure Python 3.8+ is installed
2. Navigate to the project directory
3. No additional dependencies required for basic usage
4. (Optional) Install OpenAI for real LLM: `pip install openai`

## Running the Example

1. Open terminal/command prompt
2. Navigate to `src` directory
3. Run: `python main.py`
4. Check outputs:
   - `report.html` - Visual report
   - `report.txt` - Audit trail
   - `report.csv` - Data extract
   - `audit_log.json` - Complete audit log

## Using in Your Own Code

```python
from main import CorepReportingAssistant

# Create assistant
assistant = CorepReportingAssistant(
    report_name="Your Report Name",
    template_id="own_funds"  # or "capital_requirements"
)

# Define scenario with your data
scenario = {
    "bank_name": "Your Bank",
    "reporting_date": "2024-12-31",
    "CET1_capital": 1500.0,
    "AT1_capital": 300.0,
    "Tier2_capital": 250.0,
}

# Ask your question
question = "Calculate total own funds"

# Process
result = assistant.process_question(question, scenario)

# Generate and save reports
html = assistant.generate_report("html")
assistant.export_audit_log("audit.json")
```

## Available Templates

1. **own_funds** - Own Funds reporting
   - Fields: CET1, AT1, Tier 1, Tier 2, Total Own Funds
   - Required for: Capital adequacy reporting

2. **capital_requirements** - Capital Requirements
   - Fields: Credit Risk, Market Risk, Operational Risk totals
   - Required for: Pillar 1 reporting

## Key Features to Explore

1. **Template Validation** - Automatic checking of completeness and consistency
2. **Audit Trail** - Complete record of which regulations supported each field
3. **Report Generation** - HTML, text, and CSV formats
4. **Confidence Scores** - See how confident the system is about each value

## Common Tasks

### Task 1: Generate Own Funds Report
```python
assistant = CorepReportingAssistant("Q4 2024", "own_funds")
result = assistant.process_question(
    "Calculate total own funds",
    {"CET1_capital": 1000, "AT1_capital": 200, "Tier2_capital": 150}
)
```

### Task 2: Export Audit Trail
```python
assistant.export_audit_log("audit.json")
# Check audit_log.json for complete compliance evidence
```

### Task 3: Get Validation Errors
```python
result = assistant.process_question(question, scenario)
if result['errors']:
    for error in result['errors']:
        print(f"Error: {error}")
```

### Task 4: Check Data Quality
```python
from template_mapper import MissingDataDetector

missing = MissingDataDetector.check_completeness(data, template)
inconsistent = MissingDataDetector.check_consistency(data, template)
```

## Testing

Run tests to verify the system:
```bash
cd tests
python test_suite.py
```

## Troubleshooting

**Issue**: "Template not found"
- **Solution**: Check template ID is valid. Use `list_templates()` to see available.

**Issue**: Missing fields in output
- **Solution**: Check scenario has all required data. See template instructions.

**Issue**: Validation errors
- **Solution**: Ensure all required fields are populated with valid types.

## Next Steps

1. Review README.md for full documentation
2. Examine test_suite.py for usage examples
3. Check generated audit logs to understand audit trail
4. Explore adding custom templates or rules
5. Integrate with real OpenAI API for actual LLM processing

## Support

Refer to:
- README.md for architecture and design
- Docstrings in source files for API details
- test_suite.py for integration examples
- Regulatory documents for rule interpretations
