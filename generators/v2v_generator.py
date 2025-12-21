import os
from utils.file_utils import is_image, is_video, list_valid
from models.config_model import Workflow

class V2VGenerator:
    def __init__(self, comfy_client, workflow_config: Workflow, input_base_folder: str):
        self.client = comfy_client
        self.workflow: Workflow = workflow_config
        self.input_base_folder = input_base_folder

        # Paths
        self.output_base_folder = self.client.output_folder

    def construct_jobs(self):
        videos = list_valid(self.workflow.src_video_folder, is_video)
        backgrounds = list_valid(self.workflow.background_folder, is_image)
        influencer_images = {}

        # Preload all influencer images
        for influencer_name in self.workflow.influencers:
            influencer_dir = os.path.join(self.input_base_folder, influencer_name)
            if os.path.isdir(influencer_dir):
                influencer_images[influencer_name] = list_valid(influencer_dir, is_image)
            else:
                influencer_images[influencer_name] = []

        for video in videos:
            for background in backgrounds:
                # Interleave influencers
                max_images = max(len(imgs) for imgs in influencer_images.values())
                for i in range(max_images):
                    for influencer_name, imgs in influencer_images.items():
                        if i < len(imgs):
                            yield {
                                "video": video,
                                "background": background,
                                "person": imgs[i],
                                "name": influencer_name
                            }

    def run_batch(self):
        jobs = list(self.construct_jobs())
        print(f"[V2V] Jobs found: {len(jobs)}")
        for job in jobs:
            try:
                output_subfolder = os.path.join("v2v", job["name"])
                os.makedirs(os.path.join(self.output_base_folder, output_subfolder), exist_ok=True)

                inputs = {
                    "video": job["video"],
                    "background": job["background"],
                    "person": job["person"]
                }

                print(f"\n[V2V] Starting job:")
                print(f"       Influencer: {job['name']}")
                print(f"       Video: {os.path.basename(job['video'])}")
                print(f"       Background: {os.path.basename(job['background'])}")
                print(f"       Person Image: {os.path.basename(job['person'])}")

                output_file = self.client.generate_animate_workflow(
                    workflow=self.workflow,
                    inputs=inputs,
                    output_subfolder=output_subfolder
                )

                print(f"[V2V] ✔ {output_file}")
            except Exception as e:
                print(f"[V2V] ✖ ERROR ({job['name']}): {e}")

    def run(self):
        print("[V2VGenerator] Starting V2V batch...")
        try:
            self.run_batch()
        except KeyboardInterrupt:
            print("[V2VGenerator] Interrupted by user")
