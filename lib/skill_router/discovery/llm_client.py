"""Claude Haiku client for LLM-based skill discovery.

Invokes the Anthropic Claude API for intelligent task/skill selection.
"""
import os
from typing import Optional
from lib.skill_router.interfaces.discovery import ILLMClient
from lib.skill_router.discovery.models import LLMResponse
from lib.skill_router.exceptions import (
    LLMClientError,
    RateLimitError,
    AuthenticationError,
    TimeoutError
)


class ClaudeHaikuClient(ILLMClient):
    """Client for invoking Claude Haiku API.

    Uses claude-3-5-haiku-20241022 model for fast, cost-effective
    skill discovery with structured JSON responses.
    """

    MODEL_ID = "claude-3-5-haiku-20241022"
    MAX_TOKENS = 300

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude Haiku client.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var

        Raises:
            AuthenticationError: If no API key provided and env var not set
        """
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise AuthenticationError("No API key provided and ANTHROPIC_API_KEY env var not set")

    def invoke(self, prompt: str) -> LLMResponse:
        """Invoke Claude Haiku with a prompt and return the response.

        Args:
            prompt: The prompt string to send to the LLM

        Returns:
            LLMResponse containing the response text and metadata

        Raises:
            AuthenticationError: If API authentication fails (401)
            RateLimitError: If API rate limit exceeded (429)
            TimeoutError: If API request times out
            LLMClientError: For other API failures
        """
        try:
            import anthropic
        except ImportError:
            raise LLMClientError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

        try:
            client = anthropic.Anthropic(api_key=self._api_key)

            response = client.messages.create(
                model=self.MODEL_ID,
                max_tokens=self.MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract response text from content blocks
            response_text = ""
            if response.content:
                # Claude API returns content as a list of content blocks
                for block in response.content:
                    if hasattr(block, 'text'):
                        response_text += block.text

            return LLMResponse(
                text=response_text,
                model=response.model,
                prompt_tokens=response.usage.input_tokens if response.usage else None,
                completion_tokens=response.usage.output_tokens if response.usage else None,
                finish_reason=response.stop_reason if hasattr(response, 'stop_reason') else None
            )

        except anthropic.AuthenticationError as e:
            raise AuthenticationError(f"API authentication failed: {str(e)}")
        except anthropic.RateLimitError as e:
            raise RateLimitError(f"API rate limit exceeded: {str(e)}")
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            raise TimeoutError(f"API request timed out or connection failed: {str(e)}")
        except anthropic.APIError as e:
            raise LLMClientError(f"API error: {str(e)}")
        except Exception as e:
            raise LLMClientError(f"Unexpected error invoking LLM: {str(e)}")
