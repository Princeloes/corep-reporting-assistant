"""
Test Suite for COREP Reporting Assistant

Tests for core functionality including:
- Schema validation
- Rule retrieval
- LLM processing
- Template mapping
- Audit logging
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from corep_schema import (
    CorepTemplate, FieldDefinition, DataType, ValidationRule,
    get_template, list_templates, create_own_funds_template
)
from pra_retrieval import PraRuleBook, RegulatoryRule
from llm_processor import MockLLMProcessor, ProcessingRequest
from template_mapper import TemplateValidator, CorepReportGenerator, MissingDataDetector
from audit_logger import AuditLog, AuditLogEntry


class TestCorepSchema(unittest.TestCase):
    """Test COREP schema definitions."""
    
    def test_template_loading(self):
        """Test that templates can be loaded."""
        template = get_template("own_funds")
        self.assertIsNotNone(template)
        self.assertEqual(template.template_id, "OF")
    
    def test_list_templates(self):
        """Test template listing."""
        templates = list_templates()
        self.assertIn("own_funds", templates)
        self.assertIn("capital_requirements", templates)
    
    def test_field_validation(self):
        """Test field validation."""
        field = FieldDefinition(
            field_id="TEST_001",
            field_name="Test Field",
            description="A test field",
            data_type=DataType.DECIMAL,
            required=True,
            validations=[
                {"type": ValidationRule.MIN_VALUE.value, "value": 0}
            ]
        )
        
        # Valid value
        is_valid, msg = field.validate(100.5)
        self.assertTrue(is_valid)
        
        # Invalid negative value
        is_valid, msg = field.validate(-50)
        self.assertFalse(is_valid)
        
        # Required field
        is_valid, msg = field.validate(None)
        self.assertFalse(is_valid)
    
    def test_template_validation(self):
        """Test template-level validation."""
        template = get_template("own_funds")
        
        # Valid data
        valid_data = {
            "OF_101": 1000,
            "OF_102": 200,
            "OF_103": 1200,
            "OF_201": 150,
            "OF_300": 1350,
            "OF_301": "2024-12-31"
        }
        
        is_valid, errors = template.validate_data(valid_data)
        self.assertTrue(is_valid)


class TestPraRuleBook(unittest.TestCase):
    """Test PRA rule retrieval."""
    
    def setUp(self):
        self.rulebook = PraRuleBook()
    
    def test_rule_search_by_keyword(self):
        """Test keyword search."""
        results = self.rulebook.search_by_keyword("CET1")
        self.assertGreater(len(results), 0)
    
    def test_rule_search_by_source(self):
        """Test source search."""
        results = self.rulebook.search_by_source("CRR")
        self.assertGreater(len(results), 0)
    
    def test_get_rules_for_template(self):
        """Test getting rules for a template."""
        rules = self.rulebook.get_rules_for_template("own_funds")
        self.assertGreater(len(rules), 0)


class TestLlmProcessor(unittest.TestCase):
    """Test LLM processing."""
    
    def setUp(self):
        self.processor = MockLLMProcessor()
    
    def test_process_own_funds_request(self):
        """Test processing an own funds request."""
        rulebook = PraRuleBook()
        
        request = ProcessingRequest(
            question="Calculate total own funds",
            scenario={
                "CET1_capital": 1000,
                "AT1_capital": 200,
                "Tier2_capital": 150,
                "reporting_date": "2024-12-31"
            },
            template_id="own_funds",
            relevant_rules=rulebook.get_rules_for_template("own_funds")
        )
        
        result = self.processor.process(request)
        
        # Check structure
        self.assertIsNotNone(result.structured_output)
        self.assertIsNotNone(result.confidence_scores)
        self.assertIsNotNone(result.justifications)
        
        # Check fields were populated
        self.assertIn("OF_101", result.structured_output)
        self.assertIn("OF_300", result.structured_output)


class TestTemplateValidator(unittest.TestCase):
    """Test template validation."""
    
    def setUp(self):
        self.template = get_template("own_funds")
        self.validator = TemplateValidator(self.template)
    
    def test_validate_complete_data(self):
        """Test validation of complete data."""
        data = {
            "OF_101": 1000,
            "OF_102": 200,
            "OF_103": 1200,
            "OF_201": 150,
            "OF_300": 1350,
            "OF_301": "2024-12-31"
        }
        
        is_valid, errors = self.validator.validate_data(data)
        self.assertTrue(is_valid)
    
    def test_validate_missing_required(self):
        """Test validation catches missing required fields."""
        data = {
            "OF_101": 1000,
            # Missing other required fields
        }
        
        is_valid, errors = self.validator.validate_data(data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestReportGenerator(unittest.TestCase):
    """Test report generation."""
    
    def setUp(self):
        self.template = get_template("own_funds")
        self.generator = CorepReportGenerator(self.template)
        self.data = {
            "OF_101": 1000,
            "OF_102": 200,
            "OF_103": 1200,
            "OF_201": 150,
            "OF_300": 1350,
            "OF_301": "2024-12-31"
        }
    
    def test_generate_html_report(self):
        """Test HTML report generation."""
        html = self.generator.generate_html_report(self.data)
        
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Own Funds", html)
        self.assertIn("OF_101", html)
    
    def test_generate_text_report(self):
        """Test text report generation."""
        text = self.generator.generate_text_report(self.data)
        
        self.assertIn("Own Funds", text)
        self.assertIn("OF_101", text)
    
    def test_generate_csv_report(self):
        """Test CSV report generation."""
        csv = self.generator.generate_csv_extract(self.data)
        
        self.assertIn("Field ID", csv)
        self.assertIn("OF_101", csv)
        self.assertIn("Value", csv)


class TestAuditLog(unittest.TestCase):
    """Test audit logging."""
    
    def setUp(self):
        self.audit_log = AuditLog("Test Report", "own_funds")
    
    def test_log_entry(self):
        """Test logging an entry."""
        self.audit_log.log(
            action="UPDATE",
            field_id="OF_101",
            new_value=1000,
            regulatory_reference="CRR_50_1"
        )
        
        self.assertEqual(len(self.audit_log.entries), 1)
    
    def test_field_history(self):
        """Test field history tracking."""
        self.audit_log.log(
            action="UPDATE",
            field_id="OF_101",
            old_value=0,
            new_value=1000,
            regulatory_reference="CRR_50_1"
        )
        
        history = self.audit_log.get_field_history("OF_101")
        self.assertEqual(len(history), 1)
    
    def test_rule_usage_tracking(self):
        """Test rule usage counting."""
        self.audit_log.log(
            action="UPDATE",
            regulatory_reference="CRR_50_1"
        )
        self.audit_log.log(
            action="UPDATE",
            regulatory_reference="CRR_50_1"
        )
        
        rules = self.audit_log.get_rules_used()
        self.assertEqual(rules["CRR_50_1"], 2)
    
    def test_audit_report(self):
        """Test audit report generation."""
        self.audit_log.log(
            action="UPDATE",
            field_id="OF_101",
            new_value=1000
        )
        
        report = self.audit_log.generate_audit_report()
        self.assertIn("COREP REPORTING AUDIT LOG", report)
        self.assertIn("UPDATE", report)


class TestMissingDataDetector(unittest.TestCase):
    """Test missing data detection."""
    
    def setUp(self):
        self.template = get_template("own_funds")
    
    def test_detect_missing_required_fields(self):
        """Test detection of missing required fields."""
        incomplete_data = {
            "OF_101": 1000,
            # Missing required fields
        }
        
        missing = MissingDataDetector.check_completeness(incomplete_data, self.template)
        self.assertGreater(len(missing), 0)
    
    def test_detect_consistency_issues(self):
        """Test detection of consistency issues."""
        inconsistent_data = {
            "OF_101": 1000,
            "OF_102": 200,
            "OF_103": 1000,  # Should equal 1200 (1000 + 200)
            "OF_201": 150,
            "OF_300": 1350,
            "OF_301": "2024-12-31"
        }
        
        issues = MissingDataDetector.check_consistency(inconsistent_data, self.template)
        self.assertGreater(len(issues), 0)


def run_all_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_all_tests()
