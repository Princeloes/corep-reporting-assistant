"""
LLM Interface and Processing Module

This module handles:
1. Communication with LLMs (OpenAI/Anthropic)
2. Prompt construction with regulatory context
3. Structured output generation aligned to schemas
4. Error handling and fallback mechanisms
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json
from abc import ABC, abstractmethod

from corep_schema import CorepTemplate, FieldDefinition
from pra_retrieval import RegulatoryRule, get_rulebook


@dataclass
class ProcessingRequest:
    """Represents a regulatory reporting request."""
    
    question: str
    scenario: Dict[str, Any]
    template_id: str
    relevant_rules: List[RegulatoryRule]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "scenario": self.scenario,
            "template_id": self.template_id,
            "relevant_rules": [r.to_dict() for r in self.relevant_rules]
        }


@dataclass
class ProcessingResult:
    """Represents the result of LLM processing."""
    
    structured_output: Dict[str, Any]
    confidence_scores: Dict[str, float]
    justifications: Dict[str, List[str]]  # Field -> [rule_ids]
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "structured_output": self.structured_output,
            "confidence_scores": self.confidence_scores,
            "justifications": self.justifications,
            "errors": self.errors,
            "warnings": self.warnings
        }


class LLMProcessor(ABC):
    """Abstract base class for LLM processors."""
    
    @abstractmethod
    def process(self, request: ProcessingRequest) -> ProcessingResult:
        """
        Process a regulatory reporting request.
        
        Args:
            request: The processing request
            
        Returns:
            ProcessingResult with structured output
        """
        pass
    
    def construct_prompt(self, request: ProcessingRequest, 
                        template: CorepTemplate) -> str:
        """
        Construct a prompt for the LLM.
        
        Args:
            request: The processing request
            template: The target COREP template
            
        Returns:
            Formatted prompt string
        """
        
        # Build regulatory context
        regulatory_context = "## RELEVANT REGULATORY RULES\n\n"
        for rule in request.relevant_rules:
            regulatory_context += f"""
### {rule.section} - {rule.title}
Source: {rule.source}

{rule.content}

---
"""
        
        # Build template schema
        schema_context = "## TARGET COREP TEMPLATE SCHEMA\n\n"
        schema_context += f"Template: {template.template_name}\n"
        schema_context += f"Description: {template.description}\n\n"
        schema_context += "### Required Fields:\n"
        
        for field_id, field_def in template.fields.items():
            schema_context += f"""
- **{field_id}**: {field_def.field_name}
  - Type: {field_def.data_type.value}
  - Required: {field_def.required}
  - Instructions: {field_def.instructions}
  - Reference: {field_def.regulatory_reference}
"""
        
        # Build scenario information
        scenario_context = "## REPORTING SCENARIO\n\n"
        scenario_context += "```json\n"
        scenario_context += json.dumps(request.scenario, indent=2)
        scenario_context += "\n```\n"
        
        # Construct full prompt
        prompt = f"""
You are an expert regulatory reporting assistant specializing in PRA COREP reporting.

## TASK
Based on the user's question and the provided reporting scenario, extract or calculate the 
required values for the COREP template fields. Your output must be valid structured JSON 
aligned exactly to the template schema.

## USER QUESTION
{request.question}

{regulatory_context}

{schema_context}

{scenario_context}

## INSTRUCTIONS
1. Extract values from the scenario that map to template fields
2. Calculate derived fields (e.g., totals) as required
3. For each field, identify which regulatory rules justify its value
4. Output ONLY valid JSON in the format specified below
5. If a value cannot be determined, use null and explain in a note

## REQUIRED OUTPUT FORMAT
Output must be a JSON object with this structure:
{{
  "field_values": {{
    "FIELD_ID_1": value,
    "FIELD_ID_2": value,
    ...
  }},
  "confidence_scores": {{
    "FIELD_ID_1": 0.95,
    ...
  }},
  "justifications": {{
    "FIELD_ID_1": ["RULE_ID_1", "RULE_ID_2"],
    ...
  }},
  "notes": ["Any explanations or assumptions made"],
  "data_quality_issues": ["Any identified issues"]
}}

Begin your response directly with the JSON object, with no additional text.
"""
        
        return prompt


class MockLLMProcessor(LLMProcessor):
    """
    Mock LLM processor for demonstration.
    In production, this would call OpenAI API, Anthropic Claude, etc.
    """
    
    def process(self, request: ProcessingRequest) -> ProcessingResult:
        """
        Process using mock/fallback logic.
        
        Args:
            request: The processing request
            
        Returns:
            ProcessingResult with extracted/calculated values
        """
        
        structured_output = {}
        confidence_scores = {}
        justifications = {}
        errors = []
        warnings = []
        
        # Extract scenario data
        scenario = request.scenario
        
        # Map scenario fields to template fields
        # This demonstrates field extraction and calculation
        
        if request.template_id == "own_funds":
            # Extract capital values from scenario
            cet1 = scenario.get("CET1_capital", 0)
            at1 = scenario.get("AT1_capital", 0)
            tier2 = scenario.get("Tier2_capital", 0)
            
            structured_output = {
                "OF_101": cet1,
                "OF_102": at1,
                "OF_103": cet1 + at1,  # Calculated: Tier 1 Total
                "OF_201": tier2,
                "OF_300": cet1 + at1 + tier2,  # Calculated: Total Own Funds
                "OF_301": scenario.get("reporting_date", "2024-12-31")
            }
            
            # Confidence scores (would be generated by LLM)
            confidence_scores = {
                "OF_101": 0.90,
                "OF_102": 0.88,
                "OF_103": 0.95,  # Higher confidence for calculated fields
                "OF_201": 0.85,
                "OF_300": 0.95,
                "OF_301": 0.99
            }
            
            # Justifications (which rules support this field)
            justifications = {
                "OF_101": ["CRR_50_1", "PRA_RULE_1"],
                "OF_102": ["CRR_51_1", "PRA_RULE_1"],
                "OF_103": ["CRR_Article_49", "PRA_RULE_1"],
                "OF_201": ["CRR_62_1", "PRA_RULE_1"],
                "OF_300": ["CRR_Article_48", "COREP_OWN_FUNDS"],
                "OF_301": ["COREP_OWN_FUNDS"]
            }
            
            # Validation
            if cet1 is None or cet1 < 0:
                errors.append("CET1 capital must be non-negative")
            if at1 is None or at1 < 0:
                errors.append("AT1 capital must be non-negative")
            if tier2 is None or tier2 < 0:
                errors.append("Tier 2 capital must be non-negative")
            
            # Data quality warnings
            if cet1 / (cet1 + at1 + tier2) < 0.5 if (cet1 + at1 + tier2) > 0 else False:
                warnings.append("CET1 represents less than 50% of total tier 1 - unusual but not impossible")
        
        elif request.template_id == "capital_requirements":
            # Extract risk-weighted amounts
            credit_risk = scenario.get("credit_risk_requirement", 0)
            market_risk = scenario.get("market_risk_requirement", 0)
            operational_risk = scenario.get("operational_risk_requirement", 0)
            
            structured_output = {
                "CR_101": credit_risk,
                "CR_102": market_risk,
                "CR_103": operational_risk,
                "CR_200": credit_risk + market_risk + operational_risk
            }
            
            confidence_scores = {
                "CR_101": 0.92,
                "CR_102": 0.85,
                "CR_103": 0.88,
                "CR_200": 0.95
            }
            
            justifications = {
                "CR_101": ["CRR_Part_3"],
                "CR_102": ["CRR_Part_3"],
                "CR_103": ["CRR_Part_3"],
                "CR_200": ["CRR_Article_92"]
            }
        
        return ProcessingResult(
            structured_output=structured_output,
            confidence_scores=confidence_scores,
            justifications=justifications,
            errors=errors,
            warnings=warnings
        )


class RealLLMProcessor(LLMProcessor):
    """
    Real LLM processor using OpenAI API.
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with API key.
        
        Args:
            api_key: OpenAI API key (or uses environment variable)
        """
        self.api_key = api_key
        self.client = None
        
        try:
            import os
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
            
            if api_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
        except ImportError:
            print("OpenAI library not installed. Using mock processor instead.")
            # Fall back to mock processor
    
    def process(self, request: ProcessingRequest) -> ProcessingResult:
        """
        Process using OpenAI API if available, otherwise mock.
        
        Args:
            request: The processing request
            
        Returns:
            ProcessingResult with LLM-generated output
        """
        
        if not self.client:
            # Fall back to mock processor
            mock_processor = MockLLMProcessor()
            return mock_processor.process(request)
        
        try:
            # Get template
            from corep_schema import get_template
            template = get_template(request.template_id)
            
            if not template:
                raise ValueError(f"Template {request.template_id} not found")
            
            # Construct prompt
            prompt = self.construct_prompt(request, template)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert regulatory COREP reporting assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for consistency
                max_tokens=2000
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            result_data = json.loads(response_text)
            
            return ProcessingResult(
                structured_output=result_data.get("field_values", {}),
                confidence_scores=result_data.get("confidence_scores", {}),
                justifications=result_data.get("justifications", {}),
                errors=[],
                warnings=result_data.get("data_quality_issues", [])
            )
        
        except json.JSONDecodeError as e:
            return ProcessingResult(
                structured_output={},
                confidence_scores={},
                justifications={},
                errors=[f"Failed to parse LLM response: {str(e)}"],
                warnings=[]
            )
        except Exception as e:
            return ProcessingResult(
                structured_output={},
                confidence_scores={},
                justifications={},
                errors=[f"LLM processing failed: {str(e)}"],
                warnings=[]
            )


def get_processor(use_real_llm: bool = False) -> LLMProcessor:
    """
    Get an LLM processor instance.
    
    Args:
        use_real_llm: If True, attempt to use OpenAI API; if False, use mock
        
    Returns:
        LLMProcessor instance
    """
    if use_real_llm:
        return RealLLMProcessor()
    else:
        return MockLLMProcessor()
