import json
from clients.comfy_client import ComfyUIClient
from auto_generator import AutoGenerator
from models.config_model import Config
from models.config_validator import validate_config


def load_config(path: str = "config.json") -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw_config = json.load(f)
    validate_config(raw_config)
    return Config.from_dict(raw_config)


if __name__ == "__main__":
    # Load and validate config
    config: Config = load_config()

    # Initialize ComfyUI client
    comfy_client = ComfyUIClient(
        comfy_url=config.comfyui_url,
        output_folder=config.output_base_folder
    )

    # Initialize AutoGenerator with typed config
    auto_gen = AutoGenerator(
        comfy_client=comfy_client,
        config=config
    )

    # Run the active workflow
    try:
        auto_gen.run()
    finally:
        print("[Main] Shutdown complete.")
