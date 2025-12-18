import json
from clients.comfy_client import ComfyUIClient
from auto_generator import AutoGenerator
from models.config_model import Config

def load_config(path="config.json") -> Config:
    with open(path, "r") as f:
        raw_config = json.load(f)
    return Config.from_dict(raw_config)

if __name__ == "__main__":
    config = load_config()

    comfy_client = ComfyUIClient(
        comfy_url=config.comfyui_url,
        output_folder=config.output_base_folder
    )

    auto_gen = AutoGenerator(
        comfy_client=comfy_client,
        config=config
    )

    try:
        auto_gen.run()
    finally:
        print("[Main] Shutdown complete.")
