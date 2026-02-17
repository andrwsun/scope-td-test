from pydantic import Field
from scope.core.pipelines.base_schema import BasePipelineConfig, ModeDefaults, ui_field_config


class TDTestConfig(BasePipelineConfig):
    """Minimal test plugin for TouchDesigner communication."""

    pipeline_id = "td-test"
    pipeline_name = "TD Test"
    pipeline_description = "Receives messages from TouchDesigner via HTTP"

    modes = {"text": ModeDefaults(default=True)}

    # Simple text display parameter
    message: str = Field(
        default="Waiting for TouchDesigner...",
        description="Message received from TouchDesigner",
        json_schema_extra=ui_field_config(order=0, label="Current Message"),
    )

    # HTTP server port
    http_port: int = Field(
        default=5555,
        ge=1024,
        le=65535,
        description="HTTP server port for receiving TD messages",
        json_schema_extra=ui_field_config(order=1, label="HTTP Port"),
    )
