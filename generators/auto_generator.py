from generators.v2v_generator import V2VGenerator
from generators.text2image_generator import Text2ImageGenerator

class AutoGenerator:
    def __init__(self, comfy_client, config):
        self.comfy_client = comfy_client
        self.config = config

    def run(self):
        active_name = self.config.active_workflow
        workflow = next((wf for wf in self.config.workflows if wf["name"] == active_name), None)

        if not workflow:
            raise ValueError(f"Active workflow '{active_name}' not found in config.")

        wf_type = workflow["type"]
        print(f"[AutoGenerator] Running workflow: {workflow['name']} ({wf_type})")

        if wf_type == "v2v":
            gen = V2VGenerator(self.comfy_client, workflow, input_base_folder = self.config.input_base_folder)
            gen.run()
        elif wf_type == "t2i":
            gen = Text2ImageGenerator(self.comfy_client, workflow)
            gen.run()
        else:
            raise ValueError(f"Unknown workflow type: {wf_type}")
