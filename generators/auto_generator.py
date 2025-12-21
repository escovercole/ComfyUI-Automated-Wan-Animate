from typing import Union
from clients.comfy_client import ComfyUIClient
from models.config_model import Config, Workflow
from generators.v2v_generator import V2VGenerator
from generators.text2image_generator import Text2ImageGenerator
from generators.t2i_v2v_generator import T2IV2VGenerator

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

        elif workflow.type == "t2i_then_v2v":
            t2i_workflow = next(wf for wf in self.config.workflows if wf.name == workflow.t2i_workflow)
            v2v_workflow = next(wf for wf in self.config.workflows if wf.name == workflow.v2v_workflow)

            gen = T2IV2VGenerator(
                comfy_client=self.comfy_client,
                t2i_workflow=t2i_workflow,
                v2v_workflow=v2v_workflow,
                input_base_folder=self.input_base_folder
            )
            gen.run()


        else:
            raise ValueError(f"Unknown workflow type: {workflow.type}")
