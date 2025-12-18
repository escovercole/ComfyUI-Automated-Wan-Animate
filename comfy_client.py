import subprocess
import os
import json
import time
import requests
import random
from datetime import datetime
import cv2
import math

class ComfyUIClient:
    def __init__(self, config):
        self.config = config
        self.comfy_url = config["comfyui_url"].rstrip("/") 
        self.workflow = config["workflow"]
        self.output_folder = config["output_base_folder"]


    def load_workflow(self, workflow_path):
        print("Loading workflow:", workflow_path)
        with open(workflow_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _post_workflow(self, workflow):
        """POST a workflow to ComfyUI and return the prompt_id."""
        url = f"{self.comfy_url}/api/prompt"

        workflow = {"prompt": workflow}
        data = json.dumps(workflow).encode('utf-8')

        response = requests.post(url, data=data)

        if response.status_code != 200:
            raise RuntimeError(f"Error sending workflow: {response.text}")

        data = response.json()
        return data["prompt_id"]

    def _wait_for_result(self, prompt_id):
        """Poll /api/history/<prompt_id> until results are ready."""
        history_url = f"{self.comfy_url}/api/history/{prompt_id}"

        while True:
            time.sleep(0.5)
            r = requests.get(history_url)
            if r.status_code == 200:
                data = r.json()
                if prompt_id in data:
                    return data[prompt_id]

    def submit_workflow(self, workflow):
        prompt_id = self._post_workflow(workflow)
        return self._wait_for_result(prompt_id)

    def _download_image(self, filename, save_path):
        url = f"{self.comfy_url}/api/view?filename={filename}&type=output"
        r = requests.get(url)
        if r.status_code != 200:
            raise RuntimeError(f"Error downloading image: {r.text}")

        with open(save_path, "wb") as f:
            f.write(r.content)

    @staticmethod
    def get_frame_count_for_16fps(video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")

        orig_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        frame_count_16fps = math.ceil(total_frames * 16 / orig_fps)
        return frame_count_16fps    


    def generate_animate_workflow(
        self,
        workflow_name,
        inputs: dict,
        output_subfolder: str
    ):
        workflow_config = self.config["workflows"][workflow_name]
        workflow_file = workflow_config["file"]
        node_map = workflow_config["inputs"]
        output_node = workflow_config["output_node"]

        workflow = self.load_workflow(workflow_file)

        for key, node_id in node_map.items():
            if key in inputs:
                node_input_name = "image" if "image" in key or "video" in key else key
                workflow[str(node_id)]["inputs"][node_input_name] = inputs[key]

        video_path = inputs.get("video")
        if video_path:
            if "num_frames" in node_map:
                frame_count = self.get_frame_count_for_16fps(video_path)
                workflow[str(node_map["num_frames"])]["inputs"]["num_frames"] = frame_count
            if "frame_window_size" in node_map:
                workflow[str(node_map["frame_window_size"])]["inputs"]["frame_window_size"] = frame_count

        result = self.submit_workflow(workflow)
        video_info = result["outputs"][str(output_node)]["gifs"][0]
        video_path = video_info["fullpath"]

        output_path = os.path.join(self.output_folder, output_subfolder)
        os.makedirs(output_path, exist_ok=True)
        output_file = os.path.join(output_path, datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4")
        self._download_image(video_path, output_file)

        return output_file


