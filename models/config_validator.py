class ConfigValidationError(Exception):
    pass


def validate_config(cfg: dict):
    required_root = [
        "comfyui_url",
        "paths",
        "active_workflow",
        "workflows"
    ]

    for key in required_root:
        if key not in cfg:
            raise ConfigValidationError(f"Missing root config key: '{key}'")

    if not isinstance(cfg["workflows"], list) or not cfg["workflows"]:
        raise ConfigValidationError("workflows must be a non-empty list")

    workflow_names = set()
    for wf in cfg["workflows"]:
        validate_workflow(wf, workflow_names)

    active = cfg["active_workflow"]
    if active not in workflow_names:
        raise ConfigValidationError(
            f"active_workflow '{active}' does not match any workflow name"
        )


def validate_workflow(wf: dict, workflow_names: set):
    for key in ("name", "type", "workflow_file"):
        if key not in wf:
            raise ConfigValidationError(
                f"Workflow missing required key '{key}'"
            )

    if wf["name"] in workflow_names:
        raise ConfigValidationError(f"Duplicate workflow name: {wf['name']}")

    workflow_names.add(wf["name"])

    if wf["type"] == "t2i":
        validate_t2i(wf)
    elif wf["type"] == "v2v":
        validate_v2v(wf)
    else:
        raise ConfigValidationError(f"Unknown workflow type: {wf['type']}")


def validate_t2i(wf: dict):
    for key in ("nodes", "influencers", "prompt_set"):
        if key not in wf:
            raise ConfigValidationError(
                f"T2I workflow '{wf['name']}' missing '{key}'"
            )

    for node in ("prompt", "lora", "model", "seed"):
        if node not in wf["nodes"]:
            raise ConfigValidationError(
                f"T2I workflow '{wf['name']}' missing node '{node}'"
            )


def validate_v2v(wf: dict):
    for key in ("inputs", "output_node", "influencers"):
        if key not in wf:
            raise ConfigValidationError(
                f"V2V workflow '{wf['name']}' missing '{key}'"
            )
