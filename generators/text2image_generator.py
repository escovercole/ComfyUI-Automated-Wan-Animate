import os
import random
from datetime import datetime
from clients.comfy_client import ComfyUIClient
from models.config_model import Workflow, Influencer

class Text2ImageGenerator:
    def __init__(self, comfy_client: ComfyUIClient, workflow_config: Workflow):
        """
        :param comfy_client: ComfyUIClient instance
        :param workflow_config: single T2I workflow from config (Workflow object)
        """
        self.client = comfy_client
        self.workflow: Workflow = workflow_config

        # Workflow node IDs
        self.prompt_node_id = self.workflow.prompt_node_id
        self.model_node_id = self.workflow.model_node_id
        self.lora_node_id = self.workflow.lora_node_id
        self.seed_node_id = self.workflow.seed_node_id

        self.model = self.workflow.model
        self.output_pattern = self.workflow.output_filename_pattern
        self.prompts = self.workflow.prompts or []
        self.influencers: list[Influencer] = self.workflow.influencer_configs or []

    def _make_output_path(self, influencer_name: str, prompt_index: int) -> str:
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
                full_prompt = f"{influencer.keyword} {prompt}".strip() if influencer.keyword else prompt
                output_path = self._make_output_path(influencer.name, i)

                seed = random.randint(0, 2**32 - 1)

                try:
                    self.client.generate_text2image(
                        workflow=self.workflow,
                        prompt=full_prompt,
                        loras=[influencer.lora] if influencer.lora else [],
                        seed=seed,
                        output_path=output_path
                    )

                    print(f"[T2I] ✔ Saved → {output_path}")
                except Exception as e:
                    print(f"[T2I] ✖ ERROR generating '{full_prompt}' for {influencer.name}: {e}")
