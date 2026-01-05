"""JSON response parser for LLM skill discovery.

Parses LLM responses into structured DiscoveryResult objects,
handling malformed JSON and validation gracefully.
"""
import json
import re
from typing import List, Dict, Any
from lib.skill_router.interfaces.discovery import IResponseParser
from lib.skill_router.discovery.models import LLMResponse, SkillMatch, DiscoveryResult
from lib.skill_router.exceptions import ParseError


class JSONResponseParser(IResponseParser):
    """Parses JSON responses from LLM into structured DiscoveryResult.

    Handles:
    - Markdown code block extraction (```json ... ```)
    - Single object or array responses
    - Field validation and error handling
    - Confidence score normalization
    """

    def parse(self, llm_response: LLMResponse) -> DiscoveryResult:
        """Parse an LLM response into a structured discovery result.

        Args:
            llm_response: The raw response from the LLM

        Returns:
            DiscoveryResult with parsed matches and metadata

        Raises:
            ParseError: If the response cannot be parsed into valid structure
        """
        try:
            # Extract JSON from response text
            json_data = self._extract_json(llm_response.text)

            # Handle both single object and array responses
            if isinstance(json_data, dict):
                matches = [self._validate_match(json_data)]
            elif isinstance(json_data, list):
                matches = [self._validate_match(item) for item in json_data]
            else:
                raise ParseError(f"Expected JSON object or array, got {type(json_data).__name__}")

            # Sort matches by confidence descending
            matches.sort(key=lambda m: m.confidence, reverse=True)

            return DiscoveryResult(
                matches=matches,
                raw_response=llm_response.text,
                model_used=llm_response.model,
                prompt_tokens=llm_response.prompt_tokens,
                completion_tokens=llm_response.completion_tokens
            )

        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse LLM response: {str(e)}")

    def _extract_json(self, text: str) -> Any:
        """Extract JSON from response text, handling markdown code blocks.

        Args:
            text: Raw response text from LLM

        Returns:
            Parsed JSON data (dict or list)

        Raises:
            ParseError: If JSON cannot be extracted or parsed
        """
        if not text or not text.strip():
            # Empty response - return empty list for empty DiscoveryResult
            return []

        # Strip markdown code blocks if present
        # Pattern: ```json\n...\n``` or ```\n...\n```
        code_block_pattern = r'```(?:json)?\s*\n(.*?)\n```'
        match = re.search(code_block_pattern, text, re.DOTALL)

        if match:
            json_text = match.group(1)
        else:
            json_text = text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON: {str(e)}")

    def _validate_match(self, match_data: Dict[str, Any]) -> SkillMatch:
        """Validate and convert match data to SkillMatch object.

        Args:
            match_data: Dictionary containing match fields

        Returns:
            Validated SkillMatch object

        Raises:
            ParseError: If required fields are missing or invalid
        """
        # Check required fields
        required_fields = ['type', 'name', 'confidence', 'reasoning']
        missing_fields = [field for field in required_fields if field not in match_data]

        if missing_fields:
            raise ParseError(f"Missing required fields: {', '.join(missing_fields)}")

        # Extract fields
        match_type = match_data['type']
        name = match_data['name']
        confidence = match_data['confidence']
        reasoning = match_data['reasoning']

        # Validate type
        if match_type not in ['task', 'skill']:
            raise ParseError(f"Invalid type '{match_type}', must be 'task' or 'skill'")

        # Validate name
        if not name or not isinstance(name, str):
            raise ParseError("name must be a non-empty string")

        # Validate confidence
        if not isinstance(confidence, (int, float)):
            raise ParseError(f"confidence must be a number, got {type(confidence).__name__}")

        # Clamp confidence to valid range if slightly out of bounds
        if confidence < 0.0:
            if confidence >= -0.01:  # Allow small floating point errors
                confidence = 0.0
            else:
                raise ParseError(f"confidence {confidence} is below 0.0")

        if confidence > 1.0:
            if confidence <= 1.01:  # Allow small floating point errors
                confidence = 1.0
            else:
                raise ParseError(f"confidence {confidence} is above 1.0")

        # Validate reasoning
        if not reasoning or not isinstance(reasoning, str):
            raise ParseError("reasoning must be a non-empty string")

        # Create SkillMatch (uses skill_name field regardless of whether it's a task or skill)
        return SkillMatch(
            skill_name=name,
            confidence=float(confidence),
            reasoning=reasoning
        )
