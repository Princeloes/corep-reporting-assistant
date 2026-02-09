"""
PRA Regulatory Rule Retrieval System

This module handles retrieval of relevant PRA Rulebook sections
and COREP instructions based on queries.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import json


@dataclass
class RegulatoryRule:
    """Represents a regulatory rule or guidance text."""
    
    rule_id: str
    section: str
    title: str
    content: str
    source: str  # e.g., "CRR Article 50", "PRA Rulebook"
    relevance_keywords: List[str]
    effective_date: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "section": self.section,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "relevance_keywords": self.relevance_keywords,
            "effective_date": self.effective_date
        }


class PraRuleBook:
    """Database and retrieval system for PRA regulatory rules."""
    
    def __init__(self):
        """Initialize the rule book with sample regulatory content."""
        self.rules: Dict[str, RegulatoryRule] = {}
        self._populate_sample_rules()
    
    def _populate_sample_rules(self):
        """Populate with sample PRA Rulebook and CRR content."""
        
        # CRR Article 50 - CET1 Definition
        self.add_rule(RegulatoryRule(
            rule_id="CRR_50_1",
            section="CRR Article 50",
            title="Definition of Common Equity Tier 1 capital",
            content="""
            Common Equity Tier 1 capital shall consist of the sum of the following items:
            
            (1) Capital items: paid-up capital instruments, share premium reserves,
            retained earnings and other reserves as defined in this regulation;
            
            (2) Adjustments to CET1 for prudential filters and deductions;
            
            (3) CET1 capital items must meet all of the following criteria:
                - They are not subject to any terms or conditions that are not allowed
                - They are eligible under CRR Article 28
                - They absorb losses immediately and fully
                - They do not carry a fixed maturity date
            """,
            source="CRR - Capital Requirements Regulation (EU) 575/2013",
            relevance_keywords=["CET1", "capital", "common equity", "tier 1"],
            effective_date="2014-01-01"
        ))
        
        # CRR Article 51 - AT1 Definition
        self.add_rule(RegulatoryRule(
            rule_id="CRR_51_1",
            section="CRR Article 51",
            title="Definition of Additional Tier 1 capital",
            content="""
            Additional Tier 1 capital shall consist of capital items that meet all of the
            following criteria:
            
            (1) They are not included in Common Equity Tier 1 capital;
            (2) They are paid-in, not subject to cancellation;
            (3) They are perpetual, with no maturity date;
            (4) They are subordinated to depositors and creditors;
            (5) They can absorb losses on a going basis;
            (6) They meet eligibility criteria of Article 28 and Article 52
            
            Additional Tier 1 capital instruments may allow for:
            - Step-ups or other incentives to redeem
            - Conversion to CET1 at predetermined ratios
            - Discretionary dividend payments
            """,
            source="CRR - Capital Requirements Regulation (EU) 575/2013",
            relevance_keywords=["AT1", "additional tier 1", "capital", "perpetual"],
            effective_date="2014-01-01"
        ))
        
        # CRR Article 62 - Tier 2 Capital
        self.add_rule(RegulatoryRule(
            rule_id="CRR_62_1",
            section="CRR Article 62",
            title="Definition of Tier 2 capital",
            content="""
            Tier 2 capital shall consist of items that meet all of the following criteria:
            
            (1) They are not included in Tier 1 capital;
            (2) They are of a subordinated nature;
            (3) They have an original maturity of at least 5 years
            (4) They are not guaranteed by a Member State or third country;
            (5) They can absorb losses in wind-down scenarios;
            (6) They meet eligibility criteria of Article 28, 63 and 66
            
            Tier 2 instruments must be:
            - Issued and fully paid
            - Freely transferable
            - Not subject to terms that would trigger early repayment
            """,
            source="CRR - Capital Requirements Regulation (EU) 575/2013",
            relevance_keywords=["Tier 2", "T2", "capital", "subordinated"],
            effective_date="2014-01-01"
        ))
        
        # PRA Rule on Own Funds
        self.add_rule(RegulatoryRule(
            rule_id="PRA_RULE_1",
            section="PRA Rulebook - Capital",
            title="Requirements for Own Funds Composition",
            content="""
            Banks subject to the PRA Rulebook must maintain Own Funds meeting the
            following minimum standards:
            
            (1) Own Funds Quality:
                - CET1 must be of the highest quality, easily convertible to cash
                - AT1 instruments must absorb losses on going concern basis
                - Tier 2 instruments must provide cushion in resolution
            
            (2) Reporting Requirements:
            - Own Funds must be reported quarterly under COREP
            - All components must be reconciled to audited financial statements
            - Any modifications to capital items must be disclosed
            
            (3) Deductions from Own Funds:
            - Prudential filters and deductions as defined in CRR Part 2
            - Own funds deductions for significant investments (>10%)
            - Cross-holding adjustments where applicable
            """,
            source="PRA Rulebook",
            relevance_keywords=["own funds", "total capital", "requirements", "PRA"],
            effective_date="2013-01-01"
        ))
        
        # COREP Reporting Instructions
        self.add_rule(RegulatoryRule(
            rule_id="COREP_OWN_FUNDS",
            section="COREP ITS 680/2014 - Annex XIII",
            title="COREP Template - Own Funds Reporting Instructions",
            content="""
            Instructions for completing the Own Funds (OF) COREP template:
            
            (1) General Principles:
            - Report Own Funds at consolidated level
            - Use year-end published financial statements
            - Apply prudential filters and deductions per CRR
            - Values must be in thousands of euros
            
            (2) Field Completion Requirements:
            - All mandatory fields must be completed
            - Supporting items must be provided for validation
            - Negative values must include appropriate explanatory notes
            - Reconciliation to audited statements required
            
            (3) Data Quality Standards:
            - Consistency checks must be performed
            - Master rules must be satisfied
            - Audit trail must document source of figures
            - Attestation from CFO/Compliance required
            """,
            source="EBA Implementing Technical Standard (ITS) 680/2014",
            relevance_keywords=["COREP", "own funds", "reporting", "template", "instructions"],
            effective_date="2014-08-01"
        ))
        
        # Capital Ratio Rules
        self.add_rule(RegulatoryRule(
            rule_id="CRR_92_1",
            section="CRR Article 92",
            title="Coverage of Risk-Weighted Exposure Amounts",
            content="""
            Institutions shall maintain capital above the minimum levels as follows:
            
            (1) Own Funds Requirement:
            - Own Funds >= 8% of Risk-Weighted Exposure Amount (RWEA)
            
            (2) Tier 1 Requirement:
            - Tier 1 Capital >= 6% of RWEA
            
            (3) CET1 Requirement:
            - CET1 Capital >= 4.5% of RWEA
            
            (4) Buffers (if applicable):
            - Capital Conservation Buffer: 2.5%
            - Countercyclical Buffer: 0-2.5%
            - G-SIB Buffer: 1-3.5%
            """,
            source="CRR - Capital Requirements Regulation (EU) 575/2013",
            relevance_keywords=["capital ratio", "minimum", "RWEA", "buffers"],
            effective_date="2014-01-01"
        ))
    
    def add_rule(self, rule: RegulatoryRule):
        """Add a regulatory rule to the database."""
        self.rules[rule.rule_id] = rule
    
    def search_by_keyword(self, keyword: str) -> List[RegulatoryRule]:
        """
        Search rules by keyword.
        
        Args:
            keyword: Search term
            
        Returns:
            List of matching rules
        """
        keyword_lower = keyword.lower()
        results = []
        
        for rule in self.rules.values():
            if (keyword_lower in rule.title.lower() or
                keyword_lower in rule.content.lower() or
                any(keyword_lower in kw.lower() for kw in rule.relevance_keywords)):
                results.append(rule)
        
        return results
    
    def search_by_source(self, source: str) -> List[RegulatoryRule]:
        """Search rules by source/regulation."""
        return [rule for rule in self.rules.values() 
                if source.lower() in rule.source.lower()]
    
    def get_rule(self, rule_id: str) -> Optional[RegulatoryRule]:
        """Retrieve a specific rule by ID."""
        return self.rules.get(rule_id)
    
    def get_rules_for_template(self, template_id: str) -> List[RegulatoryRule]:
        """
        Get all relevant rules for a given template.
        
        Args:
            template_id: The template identifier
            
        Returns:
            List of relevant rules
        """
        if template_id.lower() == "own_funds":
            return (self.search_by_keyword("own funds") +
                   self.search_by_keyword("CET1") +
                   self.search_by_keyword("Tier 1") +
                   self.search_by_keyword("Tier 2"))
        
        elif template_id.lower() == "capital_requirements":
            return self.search_by_keyword("capital requirement")
        
        return []
    
    def format_rule_for_context(self, rule: RegulatoryRule) -> str:
        """Format a rule for inclusion in LLM context."""
        return f"""
Rule ID: {rule.rule_id}
Section: {rule.section}
Title: {rule.title}
Source: {rule.source}
Content:
{rule.content}
---
"""


# Global instance
pra_rulebook = PraRuleBook()


def get_rulebook() -> PraRuleBook:
    """Get the global PRA rulebook instance."""
    return pra_rulebook
