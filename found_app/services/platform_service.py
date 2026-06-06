import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Slot


class PlatformService(QObject):
    @Slot(str)
    def revealFile(self, path: str) -> None:
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        elif sys.platform == "win32":
            # shell=True required so Explorer handles paths with spaces correctly
            subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"', shell=True)
        else:
            subprocess.Popen(["xdg-open", str(Path(path).parent)])
