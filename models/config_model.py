from typing import List, Dict
from pydantic import BaseModel, validator

class Influencer(BaseModel):
    name: str
    lora: str = None
    keyword: str = ""

class Workflow(BaseModel):
    name: str
    type: str  # "v2v" or "t2i"
    workflow_file: str = None

    # V2V-specific
    inputs: Dict[str, int] = None
    output_node: int = None
    src_video_folder: str = None
    uses_background: bool = True
    background_folder: str = None
    influencers: List[str] = None

    # T2I-specific
    model_node_id: int = None
    prompt_node_id: int = None
    negative_prompt_node_id: int = None
    lora_node_id: int = None
    seed_node_id: int = None
    model: str = None
    output_filename_pattern: str = None
    pose_styles: List[dict] = None
    outfits: List[str] = None
    influencer_configs: List[Influencer] = None

     # For t2i_then_v2v workflow
    t2i_workflow: str = None
    v2v_workflow: str = None

    # -------------------------
    # Helpers for ComfyUIClient
    # -------------------------

    def to_animate_dict(self) -> dict:
        """Return a dict suitable for generate_animate_workflow"""
        if self.type != "v2v":
            raise ValueError("to_animate_dict called on non-V2V workflow")
        return {
            "workflow_file": self.workflow_file,
            "inputs": self.inputs,
            "output_node": self.output_node
        }

    def to_text2image_nodes(self) -> dict:
        """Return node IDs for generate_text2image"""
        return {
            "prompt": self.prompt_node_id,
            "negative": self.negative_prompt_node_id,
            "seed": self.seed_node_id,
            "lora": self.lora_node_id
        }

class Config(BaseModel):
    comfyui_url: str
    input_base_folder: str
    output_base_folder: str
    active_workflow: str
    workflows: List[Workflow]

    @validator("workflows", pre=True)
    def parse_influencers(cls, v):
        for wf in v:
            if wf.get("type") == "t2i" and "influencers" in wf:
                wf["influencer_configs"] = [Influencer(**i) for i in wf.pop("influencers")]
        return v

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
