import os
import shutil
import huggingface_hub


class HFModels:
    def __init__(self, repo = "therealvul/so-vits-svc-4.0", 
            model_dir = "hf_vul_models"):
        self.model_repo = huggingface_hub.Repository(local_dir=model_dir,
            clone_from=repo, skip_lfs_files=True)
        self.repo = repo
        self.model_dir = model_dir

        self.model_folders = os.listdir(model_dir)
        self.model_folders.remove('.git')
        self.model_folders.remove('.gitattributes')

    def list_models(self):
        return self.model_folders

    # Downloads model;
    # copies config to target_dir and moves model to target_dir
    def download_model(self, model_name, target_dir):
        if not model_name in self.model_folders:
            raise Exception(model_name + " not found")
        model_dir = self.model_dir
        charpath = os.path.join(model_dir,model_name)

        gen_pt = next(x for x in os.listdir(charpath) if x.startswith("G_"))
        cfg = next(x for x in os.listdir(charpath) if x.endswith("json"))
        try:
          clust = next(x for x in os.listdir(charpath) if x.endswith("pt"))
        except StopIteration as e:
          print("Note - no cluster model for "+model_name)
          clust = None

        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        gen_dir = huggingface_hub.hf_hub_download(repo_id = self.repo,
            filename = model_name + "/" + gen_pt) # this is a symlink
        
        if clust is not None:
          clust_dir = huggingface_hub.hf_hub_download(repo_id = self.repo,
              filename = model_name + "/" + clust) # this is a symlink
          shutil.move(os.path.realpath(clust_dir), os.path.join(target_dir, clust))
          clust_out = os.path.join(target_dir, clust)
        else:
          clust_out = None

        shutil.copy(os.path.join(charpath,cfg),os.path.join(target_dir, cfg))
        shutil.move(os.path.realpath(gen_dir), os.path.join(target_dir, gen_pt))

        return {"config_path": os.path.join(target_dir,cfg),
            "generator_path": os.path.join(target_dir,gen_pt),
            "cluster_path": clust_out}