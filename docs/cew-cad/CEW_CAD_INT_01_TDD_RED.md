Task 1 causal RED target:

- live OCS vertices must be arrays `[x,y]`;
- mutation normalization must accept `result.handles`;
- MCP CallToolResult-like payload must be parsed through `model_dump()` when no direct structured dict is available.

The production adapter at base `8a509a19...` does not satisfy these three contracts.
