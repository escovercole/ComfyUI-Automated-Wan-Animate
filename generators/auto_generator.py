from typing import Union
from clients.comfy_client import ComfyUIClient
from models.config_model import Config, Workflow
from generators.v2v_generator import V2VGenerator
from generators.text2image_generator import Text2ImageGenerator

class AutoGenerator:
    def __init__(self, comfy_client: ComfyUIClient, config: Config):
        self.comfy_client = comfy_client
        self.config = config
        self.input_base_folder: str = config.input_base_folder

    def run(self) -> None:
        active_name: str = self.config.active_workflow
        workflow: Workflow = next(
            (wf for wf in self.config.workflows if wf.name == active_name),
            None
        )

        if not workflow:
            raise ValueError(f"Active workflow '{active_name}' not found in config.")

        print(f"[AutoGenerator] Running workflow: {workflow.name} ({workflow.type})")

        if workflow.type == "v2v":
            gen = V2VGenerator(
                comfy_client=self.comfy_client,
                workflow_config=workflow,
                input_base_folder=self.input_base_folder
            )
            gen.run()

        elif workflow.type == "t2i":
            gen = Text2ImageGenerator(
                comfy_client=self.comfy_client,
                workflow_config=workflow
            )
            gen.run()

        else:
            raise ValueError(f"Unknown workflow type: {workflow.type}")
