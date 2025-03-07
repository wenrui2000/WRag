from pathlib import Path
import sys

src_path = Path(__file__).resolve().parent.parent
sys.path.append(str(src_path))

import logging
import os
import tempfile
from typing import List, Optional

from common.config import settings


logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, file_path: Optional[Path] = None):
        self.path_to_files = file_path if file_path is not None else settings.file_storage_path
        self.path_to_uploads = self.path_to_files / "uploads"
        self.files: List[str] = [] # List of file _names_
        self.file_paths: List[str] = [] # List of file _paths_
        self._create_directories()
        self.add_files_and_paths()

    def _create_directories(self):
        os.makedirs(self.path_to_files, exist_ok=True)
        os.makedirs(self.path_to_uploads, exist_ok=True)

    # Build the lists of files and file paths
    def add_files_and_paths(self) -> List[str]:
        self.files: List[str] = []
        self.file_paths: List[str] = []
        for root, _, filenames in os.walk(self.path_to_files):
            for filename in filenames:
                if not filename.startswith('.'):
                    full_path = os.path.join(root, filename)
                    if os.path.isfile(full_path):
                        self.files.append(filename)
                        self.file_paths.append(full_path)
        logger.info(f"File paths: {self.file_paths}")
        logger.info(f"Found {len(self.files)} files")
        return self.files

    def save_file(self, filename: str, contents: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, dir=self.path_to_uploads) as temp_file:
            temp_file.write(contents)
            temp_full_path = temp_file.name

        final_full_path = os.path.join(self.path_to_uploads, filename)

        def update_file_list(file_list, item):
            if item in file_list:
                file_list.remove(item)
            file_list.append(item)

        update_file_list(self.files, filename)
        update_file_list(self.file_paths, final_full_path)

        logger.debug(f"Saving {temp_full_path} to {final_full_path}")

        os.replace(temp_full_path, final_full_path)

        return final_full_path
