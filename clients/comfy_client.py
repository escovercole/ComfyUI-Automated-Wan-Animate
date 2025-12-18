import json
import os
import time
import requests
import cv2
import math
from datetime import datetime

class ComfyUIClient:
    def __init__(self, comfy_url: str, output_folder: str):
        self.comfy_url = comfy_url.rstrip("/")
        self.output_folder = output_folder

    def load_workflow(self, workflow_path: str):
        with open(workflow_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _post_workflow(self, workflow: dict):
        url = f"{self.comfy_url}/api/prompt"
        response = requests.post(url, json={"prompt": workflow})
        if response.status_code != 200:
            raise RuntimeError(f"Error sending workflow: {response.text}")
        return response.json()["prompt_id"]

    def _wait_for_result(self, prompt_id: str):
        history_url = f"{self.comfy_url}/api/history/{prompt_id}"
        while True:
            time.sleep(0.5)
            r = requests.get(history_url)
            if r.status_code == 200:
                data = r.json()
                if prompt_id in data:
                    return data[prompt_id]

    def submit_workflow(self, workflow: dict):
        prompt_id = self._post_workflow(workflow)
        return self._wait_for_result(prompt_id)

    def _download_file(self, filename: str, save_path: str):
        url = f"{self.comfy_url}/api/view?filename={filename}&type=output"
        r = requests.get(url)
        if r.status_code != 200:
            raise RuntimeError(f"Error downloading file: {r.text}")
        with open(save_path, "wb") as f:
            f.write(r.content)

    @staticmethod
    def get_frame_count_for_16fps(video_path: str) -> int:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")
        orig_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return math.ceil(total_frames * 16 / orig_fps)

    def generate_animate_workflow(self, workflow_config: dict, inputs: dict, output_subfolder: str):
        workflow = self.load_workflow(workflow_config["workflow_file"])

        for key, node_id in workflow_config["inputs"].items():
            if key in inputs:
                node_input_name = "image" if key in ("person", "background") else "video"
                workflow[str(node_id)]["inputs"][node_input_name] = inputs[key]

        video_path = inputs.get("video")
        if video_path:
            if "num_frames" in workflow_config["inputs"]:
                frame_count = self.get_frame_count_for_16fps(video_path)
                workflow[str(workflow_config["inputs"]["num_frames"])]["inputs"]["num_frames"] = frame_count

            if "frame_window_size" in workflow_config["inputs"]:
                workflow[str(workflow_config["inputs"]["frame_window_size"])]["inputs"]["frame_window_size"] = frame_count

        result = self.submit_workflow(workflow)

        output_info = result["outputs"][str(workflow_config["output_node"])]["gifs"][0]
        remote_path = output_info["fullpath"]

        output_dir = os.path.join(self.output_folder, output_subfolder)
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(
            output_dir,
            datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4"
        )

        self._download_file(remote_path, output_file)
        return output_file


    def generate_text2image(
        self,
        workflow_file,
        nodes,
        prompt,
        loras,
        model,
        seed,
        output_path
    ):
        workflow = self.load_workflow(workflow_file)

        workflow[str(nodes["prompt"])]["inputs"]["string"] = prompt
        workflow[str(nodes["model"])]["inputs"]["unet_name"] = model
        workflow[str(nodes["seed"])]["inputs"]["seed"] = seed

        lora_inputs = workflow[str(nodes["lora"])]["inputs"]
        lora_inputs.clear()

        for i, lora in enumerate(loras):
            lora_inputs[f"lora_{i+1}"] = {
                "on": True,
                "lora": lora,
                "strength": 1.0
            }

        prompt_id = self._post_workflow(workflow)
        result = self._wait_for_result(prompt_id)

        node_out = next(iter(result["outputs"].values()))
        image_name = node_out["images"][0]["filename"]

        self._download_file(image_name, output_path)
        return output_path
