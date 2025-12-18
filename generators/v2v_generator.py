import os
from utils.file_utils import is_image, is_video, list_valid

class V2VGenerator:
    def __init__(self, comfy_client, workflow_config: dict, input_base_folder: str):
        self.client = comfy_client
        self.cfg = workflow_config
        self.input_base_folder = input_base_folder

        # Workflow details
        self.workflow_file = self.cfg["workflow_file"]
        self.node_map = self.cfg["inputs"]
        self.output_node = self.cfg["output_node"]

        # Paths
        self.src_video_folder = self.cfg["src_video_folder"]
        self.background_folder = self.cfg["background_folder"]
        self.output_base_folder = self.client.output_folder

        # Influencers
        self.influencers = self.cfg["influencers"]

    # -------------------- Job construction --------------------
    def construct_jobs(self):
        videos = list_valid(self.src_video_folder, is_video)
        backgrounds = list_valid(self.background_folder, is_image)

        for video in videos:
            for background in backgrounds:
                for influencer in self.influencers:
                    influencer_dir = os.path.join(self.input_base_folder, influencer)
                    if not os.path.isdir(influencer_dir):
                        continue
                    for img in list_valid(influencer_dir, is_image):
                        yield {
                            "video": video,
                            "background": background,
                            "person": img,
                            "name": influencer
                        }

    # -------------------- Batch execution --------------------
    def run_batch(self):
        for job in self.construct_jobs():
            try:
                output_subfolder = os.path.join("v2v", job["name"])
                os.makedirs(os.path.join(self.output_base_folder, output_subfolder), exist_ok=True)

                inputs = {
                    "video": job["video"],
                    "background": job["background"],
                    "person": job["person"]
                }

                output_file = self.client.generate_animate_workflow(
                    workflow_config={
                        "workflow_file": self.workflow_file,
                        "inputs": self.node_map,
                        "output_node": self.output_node
                    },
                    inputs=inputs,
                    output_subfolder=output_subfolder
                )

                print(f"[V2V] ✔ {output_file}")

            except Exception as e:
                print(f"[V2V] ✖ ERROR ({job['name']}): {e}")

    # -------------------- Public API --------------------
    def run(self):
        print("[V2VGenerator] Starting V2V batch...")
        try:
            self.run_batch()
        except KeyboardInterrupt:
            print("[V2VGenerator] Interrupted by user")
