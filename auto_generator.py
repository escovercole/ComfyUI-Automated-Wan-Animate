import time
import os

class AutoGenerator:
    def __init__(self, comfy_client, config):
        """
        :param comfy_client: ComfyUIClient instance
        :param config: dict from config.json
        """
        self.comfy_client = comfy_client
        self.config = config
        self.input_base = config["input_base_folder"]
        self.output_base = config["output_base_folder"]

    @staticmethod
    def is_image(fn):
        return fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))

    @staticmethod
    def is_video(fn):
        return fn.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))

    @staticmethod
    def list_valid(folder, rule):
        return sorted(
            os.path.join(folder, f) for f in os.listdir(folder)
            if rule(f)
        )

    def constructJobs(self, videos, backgrounds, influencers):
        for video in videos:
            for background in backgrounds:
                for influencer in influencers:
                    influencer_dir = os.path.join(self.input_base, influencer)
                    for img in self.list_valid(influencer_dir, self.is_image):
                        yield (
                            {
                                "video": video, 
                                "background": background, 
                                "name": influencer, 
                                "img": img
                            }
                        )


    def doV2V(self):
        print("\n==============================")
        print("      V2V BATCH START")
        print("==============================\n")

        src_video_dir = self.config["src_video_folder"]
        videos = self.list_valid(src_video_dir, self.is_video)

        bg_dir = self.config["background_folder"]
        bgs = self.list_valid(bg_dir, self.is_image)

        influencers = self.config["influencers"]

        for job in self.constructJobs(videos, bgs, influencers):
            try:
                output_path = os.path.join(self.output_base, job["name"])
                os.makedirs(output_path, exist_ok=True)
                input = {
                    "video": job["video"],
                    "background": job["background"],
                    "person": job["img"]
                }
                output_path = self.comfy_client.generate_animate_workflow(
                    self.config["workflow_mode"],
                    inputs,
                    output_path
                )
                print(f"[V2V]   ✔ Done → {output_path}")
            except Exception as e:
                print(f"[V2V]   ✖ ERROR: {e}")

        print("\n==============================")
        print("      V2V BATCH COMPLETE")
        print("==============================\n")


    def run(self):
        print("[AutoGenerator] Starting generation loop...")
        try:
            self.doV2V()
            return

        except KeyboardInterrupt:
            print("[AutoGenerator] KeyboardInterrupt received. Exiting...")
