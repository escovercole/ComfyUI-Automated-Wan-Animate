# generators/t2i_v2v_generator.py

import os
import random
from datetime import datetime
from clients.comfy_client import ComfyUIClient
from models.config_model import Workflow, Influencer
from generators.text2image_generator import Text2ImageGenerator
from generators.v2v_generator import V2VGenerator
from utils.file_utils import list_valid, is_image, is_video

class T2IV2VGenerator:
    """
    Combined generator:
    1. Generate influencer images using T2I workflow.
    2. Animate those images using V2V workflow, selecting one image per influencer per video.
    """
    def __init__(
        self,
        comfy_client: ComfyUIClient,
        t2i_workflow: Workflow,
        v2v_workflow: Workflow,
        input_base_folder: str
    ):
        self.client = comfy_client
        self.t2i_workflow = t2i_workflow
        self.v2v_workflow = v2v_workflow
        self.input_base_folder = input_base_folder

        # Output paths
        self.t2i_output_folder = os.path.join(self.client.output_folder, "t2i_generated")
        os.makedirs(self.t2i_output_folder, exist_ok=True)

    def _generate_all_influencer_images(self):
        """
        Generate images for all influencers, poses, and outfits.
        Returns a dict: { influencer_name: [list_of_image_paths] }
        """
        print("[T2I→V2V] Starting influencer image generation...")
        t2i_gen = Text2ImageGenerator(
            comfy_client=self.client,
            workflow_config=self.t2i_workflow
        )

        influencer_images = {inf.name: [] for inf in self.t2i_workflow.influencer_configs}

        prompt_index = 0
        for influencer in self.t2i_workflow.influencer_configs:
            for pose in self.t2i_workflow.pose_styles:
                pose_prompt = pose["prompt"]
                for outfit in self.t2i_workflow.outfits:
                    full_prompt_parts = [pose_prompt, outfit, influencer.keyword]
                    full_prompt = ", ".join(p for p in full_prompt_parts if p).strip()

                    output_folder = os.path.join(self.t2i_output_folder, influencer.name)
                    os.makedirs(output_folder, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = os.path.join(
                        output_folder,
                        f"{influencer.name}_{prompt_index}_{timestamp}.png"
                    )
                    seed = random.randint(0, 2**32 - 1)

                    try:
                        self.client.generate_text2image(
                            workflow=self.t2i_workflow,
                            prompt=full_prompt,
                            loras=[influencer.lora] if influencer.lora else [],
                            seed=seed,
                            output_path=output_path
                        )
                        influencer_images[influencer.name].append(output_path)
                        print(f"[T2I→V2V] ✔ Generated: {influencer.name} | {pose['name']} | {outfit}")
                    except Exception as e:
                        print(f"[T2I→V2V] ✖ ERROR generating '{full_prompt}': {e}")

                    prompt_index += 1

        return influencer_images

    def _construct_v2v_jobs(self, influencer_images):
        videos = list_valid(self.v2v_workflow.src_video_folder, is_video)

        if not videos:
            raise RuntimeError("No videos found in src_video_folder")

        # Shuffle videos so order is different every run
        videos = videos[:]  # copy
        random.shuffle(videos)

        backgrounds = []
        if self.v2v_workflow.uses_background:
            backgrounds = list_valid(self.v2v_workflow.background_folder, is_image)
            if not backgrounds:
                raise RuntimeError("No backgrounds found")

        jobs = []

        for influencer_name, imgs in influencer_images.items():
            if not imgs:
                continue

            # Shuffle images so selection changes per run
            imgs = imgs[:]  # copy
            random.shuffle(imgs)

            for video in videos:
                img = random.choice(imgs)  # random image per video

                job = {
                    "video": video,
                    "person": img,
                    "name": influencer_name
                }

                if self.v2v_workflow.uses_background:
                    job["background"] = random.choice(backgrounds)

                jobs.append(job)

        # Final shuffle so influencer order is also mixed
        random.shuffle(jobs)

        print(f"[T2I→V2V] Total V2V jobs: {len(jobs)}")
        return jobs



    def run(self):
        print("[T2I→V2V] Starting full workflow...")

        # Step 1: Generate all influencer images
        influencer_images = self._generate_all_influencer_images()

        # Step 2: Construct V2V jobs
        jobs = self._construct_v2v_jobs(influencer_images)

        for job in jobs:
            try:
                output_subfolder = os.path.join("t2i_v2v", job["name"])
                os.makedirs(os.path.join(self.client.output_folder, output_subfolder), exist_ok=True)

                inputs = {
                    "video": job["video"],
                    "person": job["person"]
                }

                if "background" in job:
                    inputs["background"] = job["background"]

                print(f"\n[T2I→V2V] Starting job:")
                print(f"       Influencer: {job['name']}")
                print(f"       Video: {os.path.basename(job['video'])}")
                if "background" in job:
                    print(f"       Background: {os.path.basename(job['background'])}")
                print(f"       Person Image: {os.path.basename(job['person'])}")

                output_file = self.client.generate_animate_workflow(
                    workflow=self.v2v_workflow,
                    inputs=inputs,
                    output_subfolder=output_subfolder
                )

                print(f"[T2I→V2V] ✔ {output_file}")

            except Exception as e:
                print(f"[T2I→V2V] ✖ ERROR ({job['name']}): {e}")
