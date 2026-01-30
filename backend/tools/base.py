"""
Base Tool Interface for MCP (Model Context Protocol) Tools

All tools inherit from this base class to ensure:
- Standardized interface
- Type safety with Pydantic
- Error handling
- Logging
- Testability

Design Pattern: Template Method Pattern
- BaseTool defines the interface (invoke)
- Subclasses implement _execute (business logic)
- Input/output validation handled by base class

Example:
    class MyCustomTool(BaseTool):
        name = "my_custom_tool"
        description = "Does something useful"
        input_schema = MyInputSchema

        def _execute(self, input_data: MyInputSchema) -> ToolOutput:
            # Business logic here
            result = do_something(input_data.param1)
            return ToolOutput(success=True, data={"result": result})

    # Usage
    tool = MyCustomTool()
    result = tool.invoke({"param1": "value"})
    if result["success"]:
        print(result["data"]["result"])
"""

from typing import Any, Dict, Optional, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class ToolInput(BaseModel):
    """
    Base class for tool input validation.

    All tool-specific input schemas should inherit from this.
    Provides Pydantic validation and type safety.
    """
    class Config:
        # Allow extra fields for flexibility
        extra = "allow"
        # Use enum values for serialization
        use_enum_values = True


class ToolOutput(BaseModel):
    """
    Standardized tool output format.

    All tools return this structure for consistent error handling.

    Attributes:
        success: Whether tool execution succeeded
        error: Error message if failed (None if successful)
        data: Tool output data (None if failed)
    """
    success: bool = Field(
        default=True,
        description="Whether tool execution succeeded"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Tool output data"
    )

    class Config:
        # Allow serialization of complex types
        arbitrary_types_allowed = True


# ============================================================================
# BASE TOOL CLASS
# ============================================================================

class BaseTool(ABC):
    """
    Abstract base class for all MCP tools.

    Implements the Template Method pattern:
    1. invoke() is the public interface (template method)
    2. _execute() is implemented by subclasses (abstract method)

    Subclasses must define:
    - name: str - Tool identifier (snake_case)
    - description: str - Human-readable description
    - input_schema: Type[ToolInput] - Pydantic model for validation
    - _execute(input_data) -> ToolOutput - Business logic

    Benefits:
    - Standardized error handling
    - Automatic input validation
    - Consistent logging
    - Type safety
    - Testability (can mock _execute)
    """

    # Class attributes (must be overridden by subclasses)
    name: str = "base_tool"
    description: str = "Base tool description"
    input_schema: Type[ToolInput] = ToolInput

    def invoke(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Public interface for tool execution.

        This is the template method that:
        1. Validates input using input_schema
        2. Calls _execute() with validated input
        3. Handles errors gracefully
        4. Returns standardized output

        Args:
            input_dict: Dictionary matching input_schema

        Returns:
            Dictionary with keys:
                - success (bool): Execution status
                - error (str | None): Error message if failed
                - data (dict | None): Tool output if successful

        Example:
            result = tool.invoke({
                "param1": "value1",
                "param2": 42
            })

            if result["success"]:
                data = result["data"]
            else:
                print(f"Error: {result['error']}")
        """
        try:
            # Step 1: Validate input
            logger.debug(f"Validating input for tool: {self.name}")
            validated_input = self.input_schema(**input_dict)

            # Step 2: Execute tool logic
            logger.debug(f"Executing tool: {self.name}")
            output = self._execute(validated_input)

            # Step 3: Return output as dict
            result = output.dict()

            if result["success"]:
                logger.debug(f"Tool {self.name} succeeded")
            else:
                logger.warning(f"Tool {self.name} failed: {result['error']}")

            return result

        except Exception as e:
            # Catch all exceptions and return standardized error
            logger.error(f"Tool {self.name} raised exception: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                data=None
            ).dict()

    @abstractmethod
    def _execute(self, input_data: ToolInput) -> ToolOutput:
        """
        Internal execution logic (implemented by subclasses).

        This is where the actual tool logic lives. Subclasses implement
        this method with their specific functionality.

        Args:
            input_data: Validated input (type matches input_schema)

        Returns:
            ToolOutput with results:
                - success=True, data={...} on success
                - success=False, error="..." on failure

        Example Implementation:
            def _execute(self, input_data: MyInputSchema) -> ToolOutput:
                try:
                    result = do_work(input_data.param1)
                    return ToolOutput(
                        success=True,
                        data={"result": result}
                    )
                except Exception as e:
                    return ToolOutput(
                        success=False,
                        error=str(e),
                        data=None
                    )
        """
        pass

    def __repr__(self):
        """String representation for debugging"""
        return f"<{self.__class__.__name__}(name='{self.name}')>"

    def __str__(self):
        """Human-readable string"""
        return f"{self.name}: {self.description}"

    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LangGraph integration.

        Returns:
            Dictionary with tool metadata:
                - name: Tool identifier
                - description: Tool description
                - input_schema: Pydantic schema as JSON Schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema.schema()
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "BaseTool",
    "ToolInput",
    "ToolOutput",
]
