import os
import sys
sys.path.insert(0, "./")


class Structure_Recognition():
    def __init__(self):

        return None


class Runner():
    def __init__(self, cfg):
        self.structure_master_config = cfg['structure_master_config']
        self.structure_master_ckpt = cfg['structure_master_ckpt']
        self.end2end_result_folder = cfg['end2end_result_folder']
        self.structure_master_result_folder = cfg['structure_master_result_folder']

        self.init_structure_master()
    
    def init_structure_master(self):
        self.master_structure_inference = \
            Structure_Recognition(self.structure_master_config, self.structure_master_ckpt)

    def run(self, image_path):

        return None


if __name__ == "__main__":
    cfg = {
        "structure_master_config": "./config/table_master/table_master_ResnetExtract_Ranger_0705",
        "structure_master_ckpt": "./weights/table_master/",
        "end2end_result_folder": "",
        "structure_master_result_folder": ""
    }

    image_path = "./datasets/clean_data/thalas_0.jpg"

    runner = Runner(cfg)
    runner.run(image_path)
