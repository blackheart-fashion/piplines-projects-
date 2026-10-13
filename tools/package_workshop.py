"""Package tracked teaching sources and generated handout; exclude local secrets/deps."""

import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package():
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True,
    )
    files = [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]
    files.append(ROOT / "dist" / "workshop-days-1-2.html")
    files.append(ROOT / "output" / "pdf" / "workshop-days-1-2.pdf")
    target = ROOT / "dist" / "workshop-days-1-2.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            if path.is_file():
                archive.write(path, Path("jenkins-python-workshop") / path.relative_to(ROOT))
    print(target)


if __name__ == "__main__":
    package()
