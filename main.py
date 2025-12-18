import json
import os
from comfy_client import ComfyUIClient
from auto_generator import AutoGenerator

if __name__ == "__main__":
    with open("config.json", "r") as f:
        CONFIG = json.load(f)

    comfy_client = ComfyUIClient(CONFIG)

    auto_gen = AutoGenerator(
        comfy_client=comfy_client,
        config=CONFIG,
    )

    try:
        if auto_gen:
            print("Auto generating images")
            auto_gen.run()
    finally:
        print("[Main] Shutdown complete.")
