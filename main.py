"""
Main COREP Reporting Assistant Application

This is the main orchestrator that brings together:
- User input processing
- Rule retrieval
- LLM processing
- Template mapping
- Validation
- Audit logging
- Report generation
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from corep_schema import get_template, list_templates
from pra_retrieval import get_rulebook
from llm_processor import get_processor, ProcessingRequest
from template_mapper import (
    TemplateValidator, CorepReportGenerator, MissingDataDetector
)
from audit_logger import AuditLog


class CorepReportingAssistant:
    """
    Main class for the COREP Regulatory Reporting Assistant.
    
    Workflow:
    1. Accept user question and reporting scenario
    2. Retrieve relevant PRA Rulebook sections
    3. Process with LLM to generate structured output
    4. Validate against template schema
    5. Generate human-readable report
    6. Maintain audit log
    """
    
    def __init__(self, report_name: str, template_id: str, use_real_llm: bool = False):
        """
        Initialize the assistant.
        
        Args:
            report_name: Name of the report (e.g., "Own Funds Q4 2024")
            template_id: COREP template to use (own_funds, capital_requirements, etc.)
            use_real_llm: Whether to use real OpenAI API (default: False/mock)
        """
        
        self.report_name = report_name
        self.template_id = template_id
        self.template = get_template(template_id)
        
        if not self.template:
            raise ValueError(f"Template {template_id} not found. Available: {list_templates()}")
        
        self.rulebook = get_rulebook()
        self.llm_processor = get_processor(use_real_llm)
        
        # Initialize audit log
        self.audit_log = AuditLog(report_name, template_id)
        
        # Initialize validator and report generator
        self.validator = TemplateValidator(self.template)
        self.report_generator = CorepReportGenerator(self.template)
        
        # Storage for processing results
        self.structured_output: Dict[str, Any] = {}
        self.confidence_scores: Dict[str, float] = {}
        self.justifications: Dict[str, List[str]] = {}
        self.processing_errors: List[str] = []
    
    def process_question(self, question: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing function that orchestrates the entire workflow.
        
        Args:
            question: Natural language question about the reporting (e.g.,
                     "What is our total own funds?")
            scenario: Dictionary describing the reporting scenario with available data
            
        Returns:
            Dictionary with processing results
        """
        
        self.audit_log.log(
            action="PROCESS_START",
            notes=f"Question: {question}"
        )
        
        result = {
            "status": "success",
            "data": {},
            "errors": [],
            "warnings": [],
            "justifications": {},
            "confidence_scores": {},
            "audit_trail": None
        }
        
        try:
            # Step 1: Retrieve relevant regulatory rules
            print(f"\n[1/5] Retrieving relevant regulatory rules for {self.template_id} template...")
            relevant_rules = self.rulebook.get_rules_for_template(self.template_id)
            
            if relevant_rules:
                rule_ids = [r.rule_id for r in relevant_rules]
                self.audit_log.log_rule_retrieval(rule_ids, question, len(relevant_rules))
                print(f"  ✓ Retrieved {len(relevant_rules)} relevant rules")
            else:
                print(f"  ⚠ No specific rules found for this template")
            
            # Step 2: Process with LLM
            print(f"\n[2/5] Processing with LLM...")
            processing_request = ProcessingRequest(
                question=question,
                scenario=scenario,
                template_id=self.template_id,
                relevant_rules=relevant_rules
            )
            
            llm_result = self.llm_processor.process(processing_request)
            
            self.structured_output = llm_result.structured_output
            self.confidence_scores = llm_result.confidence_scores
            self.justifications = llm_result.justifications
            self.processing_errors = llm_result.errors
            
            if llm_result.errors:
                result["errors"].extend(llm_result.errors)
                print(f"  ⚠ Processing errors: {len(llm_result.errors)}")
            
            if llm_result.warnings:
                result["warnings"].extend(llm_result.warnings)
                print(f"  ⚠ Processing warnings: {len(llm_result.warnings)}")
            
            print(f"  ✓ Generated structured output with {len(self.structured_output)} fields")
            
            # Step 3: Log all field updates to audit trail
            print(f"\n[3/5] Logging to audit trail...")
            for field_id, value in self.structured_output.items():
                rules = self.justifications.get(field_id, [])
                self.audit_log.log_field_update(
                    field_id=field_id,
                    old_value=None,
                    new_value=value,
                    regulatory_references=rules,
                    user="LLM_PROCESSOR"
                )
            print(f"  ✓ Logged {len(self.structured_output)} field updates")
            
            # Step 4: Validate against schema
            print(f"\n[4/5] Validating against template schema...")
            is_valid, validation_errors = self.validator.validate_data(self.structured_output)
            
            for error in validation_errors:
                self.audit_log.log_validation(
                    field_id=error.field_id,
                    rule_type="schema_validation",
                    passed=(error.severity != "ERROR"),
                    expected="valid",
                    actual=error.error_message,
                    error_msg=error.error_message
                )
            
            if not is_valid:
                result["status"] = "completed_with_errors"
                result["errors"].extend([e.error_message for e in validation_errors if e.severity == "ERROR"])
                result["warnings"].extend([w.error_message for w in validation_errors if w.severity == "WARNING"])
            
            print(f"  {'✓' if is_valid else '✗'} Validation: {len([e for e in validation_errors if e.severity == 'ERROR'])} errors, "
                  f"{len([w for w in validation_errors if w.severity == 'WARNING'])} warnings")
            
            # Step 5: Check for missing/inconsistent data
            print(f"\n[5/5] Checking data completeness and consistency...")
            missing = MissingDataDetector.check_completeness(self.structured_output, self.template)
            inconsistent = MissingDataDetector.check_consistency(self.structured_output, self.template)
            
            if missing:
                result["warnings"].extend(missing)
                print(f"  ⚠ Missing fields: {len(missing)}")
            
            if inconsistent:
                result["warnings"].extend(inconsistent)
                print(f"  ⚠ Inconsistencies: {len(inconsistent)}")
            
            # Prepare result
            result["data"] = self.structured_output
            result["confidence_scores"] = self.confidence_scores
            result["justifications"] = self.justifications
            
            print(f"\n✓ Processing complete!")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            self.audit_log.log(
                action="PROCESS_ERROR",
                notes=f"Error: {str(e)}"
            )
        
        return result
    
    def generate_report(self, output_format: str = "html") -> str:
        """
        Generate a human-readable report from processed data.
        
        Args:
            output_format: 'html', 'text', or 'csv'
            
        Returns:
            Report string
        """
        
        self.audit_log.log(
            action="GENERATE_REPORT",
            notes=f"Format: {output_format}"
        )
        
        if output_format == "html":
            return self.report_generator.generate_html_report(
                self.structured_output,
                self.confidence_scores,
                self.justifications
            )
        elif output_format == "text":
            return self.report_generator.generate_text_report(
                self.structured_output,
                self.confidence_scores,
                self.justifications
            )
        elif output_format == "csv":
            return self.report_generator.generate_csv_extract(self.structured_output)
        else:
            raise ValueError(f"Unknown format: {output_format}")
    
    def export_audit_log(self, filepath: str):
        """Export audit log to file."""
        self.audit_log.export_to_file(filepath)
        print(f"Audit log exported to {filepath}")
    
    def print_audit_report(self):
        """Print human-readable audit report."""
        print(self.audit_log.generate_audit_report())
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get summary of audit log."""
        return {
            "report_name": self.audit_log.report_name,
            "template_id": self.audit_log.template_id,
            "total_entries": len(self.audit_log.entries),
            "top_rules": dict(self.audit_log.get_top_rules(5)),
            "validation_summary": self.audit_log.get_validation_summary()
        }


def run_example_own_funds_scenario():
    """Run an example Own Funds reporting scenario."""
    
    print("="*80)
    print("COREP REGULATORY REPORTING ASSISTANT - EXAMPLE")
    print("="*80)
    
    # Create assistant
    assistant = CorepReportingAssistant(
        report_name="Own Funds Q4 2024",
        template_id="own_funds",
        use_real_llm=False  # Using mock processor
    )
    
    # Define a reporting scenario
    scenario = {
        "bank_name": "Example Bank plc",
        "reporting_period": "Q4 2024",
        "reporting_date": "2024-12-31",
        "CET1_capital": 1500.0,  # in millions
        "AT1_capital": 300.0,
        "Tier2_capital": 250.0,
        "notes": "All capital measured at consolidated level"
    }
    
    # Ask a question
    question = """
    Please calculate the total own funds for our consolidated group for Q4 2024.
    We have:
    - CET1 capital of €1,500 million
    - AT1 capital of €300 million
    - Tier 2 capital of €250 million
    
    Please reference the appropriate CRR articles and PRA rules.
    """
    
    # Process the question
    print(f"\nReport Name: {assistant.report_name}")
    print(f"Template: {assistant.template_id}")
    print(f"\nQuestion: {question.strip()}")
    
    result = assistant.process_question(question, scenario)
    
    # Display results
    print(f"\n{'='*80}")
    print("PROCESSING RESULTS")
    print(f"{'='*80}")
    
    print(f"\nStatus: {result['status']}")
    print(f"\nProcessed Fields:")
    for field_id, value in result['data'].items():
        confidence = result['confidence_scores'].get(field_id, 0.0)
        rules = result['justifications'].get(field_id, [])
        
        print(f"  {field_id}: {value}")
        print(f"    Confidence: {confidence*100:.0f}%")
        if rules:
            print(f"    Rules: {', '.join(rules)}")
    
    if result['errors']:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"  ✗ {error}")
    
    if result['warnings']:
        print(f"\nWarnings ({len(result['warnings'])}):")
        for warning in result['warnings']:
            print(f"  ⚠ {warning}")
    
    # Generate HTML report
    print(f"\n{'='*80}")
    print("GENERATING REPORT")
    print(f"{'='*80}")
    
    html_report = assistant.generate_report("html")
    text_report = assistant.generate_report("text")
    csv_report = assistant.generate_report("csv")
    
    # Save reports
    with open("report.html", "w") as f:
        f.write(html_report)
    print("\n✓ HTML report saved to report.html")
    
    with open("report.txt", "w") as f:
        f.write(text_report)
    print("✓ Text report saved to report.txt")
    
    with open("report.csv", "w") as f:
        f.write(csv_report)
    print("✓ CSV report saved to report.csv")
    
    # Export audit log
    assistant.export_audit_log("audit_log.json")
    
    # Print audit report
    print(f"\n{'='*80}")
    print("AUDIT SUMMARY")
    print(f"{'='*80}\n")
    
    summary = assistant.get_audit_summary()
    print(json.dumps(summary, indent=2))
    
    print(f"\n✓ Audit log saved to audit_log.json")
    print(f"\n{'='*80}")
    print("EXAMPLE COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    run_example_own_funds_scenario()
