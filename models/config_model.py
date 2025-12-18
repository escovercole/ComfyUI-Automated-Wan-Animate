from typing import List, Dict
from pydantic import BaseModel, validator

class Influencer(BaseModel):
    name: str
    lora: str = None
    keyword: str = ""

class Workflow(BaseModel):
    name: str
    type: str  # "v2v" or "t2i"
    workflow_file: str

    # V2V-specific
    inputs: Dict[str, int] = None
    output_node: int = None
    src_video_folder: str = None
    background_folder: str = None
    influencers: List[str] = None

    # T2I-specific
    model_node_id: int = None
    prompt_node_id: int = None
    lora_node_id: int = None
    seed_node_id: int = None
    model: str = None
    output_filename_pattern: str = None
    prompts: List[str] = None
    influencer_configs: List[Influencer] = None

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
