"""
Audit Logging System

This module maintains comprehensive audit logs of all regulatory reporting decisions,
including which rules were used, when data was entered/modified, and validation results.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class AuditLogEntry:
    """Represents a single audit log entry."""
    
    timestamp: str
    action: str  # CREATE, UPDATE, VALIDATE, RETRIEVE_RULE, etc.
    field_id: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    regulatory_reference: Optional[str] = None
    user: str = "SYSTEM"
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json_str(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class ValidationEntry:
    """Records validation of a specific field."""
    
    def __init__(self, field_id: str, timestamp: str = None):
        self.field_id = field_id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.validations: List[Dict[str, Any]] = []
    
    def add_validation(self, rule_type: str, passed: bool, 
                       expected: Any, actual: Any, error_msg: Optional[str] = None):
        """Record a validation test."""
        self.validations.append({
            "rule": rule_type,
            "passed": passed,
            "expected": expected,
            "actual": actual,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "field_id": self.field_id,
            "timestamp": self.timestamp,
            "validations": self.validations
        }


class AuditLog:
    """Comprehensive audit log for regulatory reporting."""
    
    def __init__(self, report_name: str, template_id: str):
        """
        Initialize audit log.
        
        Args:
            report_name: Name of the report (e.g., "Own Funds Q4 2024")
            template_id: ID of the template being reported on
        """
        self.report_name = report_name
        self.template_id = template_id
        self.created_at = datetime.now().isoformat()
        self.entries: List[AuditLogEntry] = []
        self.rule_usage: Dict[str, int] = {}  # Count rule references
        self.field_history: Dict[str, List[AuditLogEntry]] = {}
        self.validation_results: Dict[str, ValidationEntry] = {}
    
    def log(self, action: str, field_id: Optional[str] = None,
            old_value: Optional[Any] = None, new_value: Optional[Any] = None,
            regulatory_reference: Optional[str] = None, 
            user: str = "SYSTEM", notes: Optional[str] = None):
        """
        Log an action.
        
        Args:
            action: Type of action (CREATE, UPDATE, VALIDATE, etc.)
            field_id: Field affected (if applicable)
            old_value: Previous value
            new_value: New value
            regulatory_reference: Supporting regulation/rule
            user: User performing action
            notes: Additional notes
        """
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            regulatory_reference=regulatory_reference,
            user=user,
            notes=notes
        )
        
        self.entries.append(entry)
        
        # Update field history
        if field_id:
            if field_id not in self.field_history:
                self.field_history[field_id] = []
            self.field_history[field_id].append(entry)
        
        # Track rule usage
        if regulatory_reference:
            self.rule_usage[regulatory_reference] = self.rule_usage.get(regulatory_reference, 0) + 1
    
    def log_field_update(self, field_id: str, old_value: Any, new_value: Any,
                        regulatory_references: List[str], user: str = "SYSTEM"):
        """
        Log a field value update with regulatory justification.
        
        Args:
            field_id: Field being updated
            old_value: Previous value
            new_value: New value
            regulatory_references: List of supporting rules
            user: User making the change
        """
        for ref in regulatory_references:
            self.log(
                action="UPDATE",
                field_id=field_id,
                old_value=old_value,
                new_value=new_value,
                regulatory_reference=ref,
                user=user
            )
    
    def log_rule_retrieval(self, rule_ids: List[str], query: str, count: int):
        """Log retrieval of regulatory rules."""
        self.log(
            action="RETRIEVE_RULES",
            notes=f"Retrieved {count} rules for query: {query}. Rules: {', '.join(rule_ids)}"
        )
        
        for rule_id in rule_ids:
            self.rule_usage[rule_id] = self.rule_usage.get(rule_id, 0) + 1
    
    def log_validation(self, field_id: str, rule_type: str, passed: bool,
                       expected: Any, actual: Any, error_msg: Optional[str] = None):
        """
        Log a validation check.
        
        Args:
            field_id: Field being validated
            rule_type: Type of validation rule
            passed: Whether validation passed
            expected: Expected value
            actual: Actual value
            error_msg: Error message if validation failed
        """
        if field_id not in self.validation_results:
            self.validation_results[field_id] = ValidationEntry(field_id)
        
        self.validation_results[field_id].add_validation(
            rule_type, passed, expected, actual, error_msg
        )
        
        self.log(
            action="VALIDATE",
            field_id=field_id,
            notes=f"Validation {rule_type}: {'PASSED' if passed else 'FAILED'}"
        )
    
    def get_field_history(self, field_id: str) -> List[Dict]:
        """Get complete history of a field."""
        if field_id not in self.field_history:
            return []
        
        return [entry.to_dict() for entry in self.field_history[field_id]]
    
    def get_rules_used(self) -> Dict[str, int]:
        """Get count of rule usages."""
        return self.rule_usage.copy()
    
    def get_top_rules(self, n: int = 10) -> List[tuple]:
        """Get the top N most-used rules."""
        return sorted(self.rule_usage.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        total_validations = sum(
            len(v.validations) for v in self.validation_results.values()
        )
        
        passed_validations = sum(
            sum(1 for val in v.validations if val['passed'])
            for v in self.validation_results.values()
        )
        
        return {
            "total_validations": total_validations,
            "passed": passed_validations,
            "failed": total_validations - passed_validations,
            "pass_rate": (passed_validations / total_validations * 100) if total_validations > 0 else 0
        }
    
    def to_dict(self) -> Dict:
        """Convert entire audit log to dictionary."""
        return {
            "report_name": self.report_name,
            "template_id": self.template_id,
            "created_at": self.created_at,
            "entries_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
            "field_history": {k: [e.to_dict() for e in v] 
                            for k, v in self.field_history.items()},
            "rule_usage": self.rule_usage,
            "validation_summary": self.get_validation_summary(),
            "validation_details": {k: v.to_dict() 
                                 for k, v in self.validation_results.items()}
        }
    
    def to_json_str(self) -> str:
        """Convert to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def export_to_file(self, filepath: str):
        """Export audit log to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json_str())
    
    def generate_audit_report(self) -> str:
        """Generate a human-readable audit report."""
        report = f"""
{'='*80}
COREP REPORTING AUDIT LOG
{'='*80}

Report: {self.report_name}
Template: {self.template_id}
Created: {self.created_at}

SUMMARY
{'-'*80}
Total Entries: {len(self.entries)}
Field Updates: {sum(1 for e in self.entries if e.action == 'UPDATE')}
Validations: {sum(1 for e in self.entries if e.action == 'VALIDATE')}

VALIDATION RESULTS
{'-'*80}
"""
        summary = self.get_validation_summary()
        report += f"Total Validations: {summary['total_validations']}\n"
        report += f"Passed: {summary['passed']}\n"
        report += f"Failed: {summary['failed']}\n"
        report += f"Pass Rate: {summary['pass_rate']:.1f}%\n\n"
        
        report += "TOP REGULATORY RULES USED\n"
        report += f"{'-'*80}\n"
        for rule, count in self.get_top_rules(10):
            report += f"{rule}: {count} references\n"
        
        report += f"\n{'='*80}\n"
        report += "DETAILED ENTRIES\n"
        report += f"{'='*80}\n"
        
        for entry in self.entries[-20:]:  # Last 20 entries
            report += f"\n[{entry.timestamp}] {entry.action}\n"
            if entry.field_id:
                report += f"  Field: {entry.field_id}\n"
            if entry.old_value is not None:
                report += f"  Old: {entry.old_value}\n"
            if entry.new_value is not None:
                report += f"  New: {entry.new_value}\n"
            if entry.regulatory_reference:
                report += f"  Reference: {entry.regulatory_reference}\n"
            if entry.notes:
                report += f"  Notes: {entry.notes}\n"
        
        return report
