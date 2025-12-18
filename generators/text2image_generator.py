import os
import random
from datetime import datetime
from clients.comfy_client import ComfyUIClient

class Text2ImageGenerator:
    def __init__(self, comfy_client: ComfyUIClient, workflow_config: dict):
        """
        :param comfy_client: ComfyUIClient instance
        :param workflow_config: single T2I workflow from config
        """
        self.client = comfy_client
        self.cfg = workflow_config

        # Workflow-specific config
        self.workflow_file = self.cfg["workflow_file"]
        self.prompt_node_id = self.cfg["prompt_node_id"]
        self.model_node_id = self.cfg["model_node_id"]
        self.lora_node_id = self.cfg["lora_node_id"]
        self.seed_node_id = self.cfg["seed_node_id"]
        self.model = self.cfg["model"]
        self.output_pattern = self.cfg["output_filename_pattern"]

        # Prompts shared across influencers
        self.prompts = self.cfg["prompts"]

        # Influencer definitions
        self.influencers = self.cfg["influencer_configs"]

    def _make_output_path(self, influencer_name: str, prompt_index: int):
        folder = os.path.join(self.client.output_folder, influencer_name)
        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_pattern.format(prefix=f"{influencer_name}_{prompt_index}", timestamp=timestamp)
        return os.path.join(folder, filename)

    def run(self):
        print(f"[T2I] Starting text-to-image generation for {len(self.influencers)} influencers...")

        for influencer in self.influencers:
            print(f"[T2I] Generating for influencer: {influencer.name}")
            for i, prompt in enumerate(self.prompts):
                full_prompt = f"{influencer.keyword} {prompt}" if influencer.keyword else prompt
                output_path = self._make_output_path(influencer.name, i)

                seed = random.randint(0, 2**32 - 1)

                try:
                    self.client.generate_text2image(
                        workflow_file=self.workflow_file,
                        nodes={
                            "prompt": self.prompt_node_id,
                            "model": self.model_node_id,
                            "lora": self.lora_node_id,
                            "seed": self.seed_node_id
                        },
                        prompt=full_prompt,
                        loras=[influencer.lora] if influencer.lora else [],
                        model=self.model,
                        seed=seed,
                        output_path=output_path
                    )
                    print(f"[T2I] ✔ Saved → {output_path}")
                except Exception as e:
                    print(f"[T2I] ✖ ERROR generating '{full_prompt}' for {influencer.name}: {e}")
