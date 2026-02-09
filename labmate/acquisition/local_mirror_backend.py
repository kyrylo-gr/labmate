from pathlib import Path
import shutil
from labmate.acquisition.backend import AcquisitionBackend

class MirrorDirectoryBackend(AcquisitionBackend):
    def __init__(self, mirror_root: str | Path):
        self._mirror_root = Path(mirror_root)

    def save_snapshot(self, acquisition) -> None:
        source_prefix = Path(acquisition.filepath)  
        source_dir = source_prefix.parent            
        prefix_name = source_prefix.name             

        destination_dir = self._mirror_root / source_dir.name
        destination_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files starting with prefix_name 
        for src in source_dir.glob(f"{prefix_name}*"):
            if src.is_file():
                shutil.copy2(src, destination_dir / src.name)

    def ensure_local_file(self, filepath: str) -> bool:
        target = Path(filepath)                      
        mirror_path = self._mirror_root / target.parent.name / target.name

        if not mirror_path.exists():
            return False

        print(f"[mirror-backend] Restoring {target} from mirror")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mirror_path, target)
        return True
