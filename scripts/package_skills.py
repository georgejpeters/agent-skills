"""Zip each skill for upload to claude.ai (Settings -> Capabilities -> Skills).

    python3 scripts/package_skills.py      -> dist/<skill>.zip

A skill from a plugin with a lib/ directory also carries that lib (e.g. quantkit.py).
Evals and caches are left out.
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"evals", "__pycache__"}


def add_tree(zf, src, arcroot):
    for f in sorted(src.rglob("*")):
        if f.is_file() and not SKIP & set(f.relative_to(src).parts) and f.name != ".DS_Store":
            zf.write(f, f"{arcroot}/{f.relative_to(src)}")


def main():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for skill in sorted(ROOT.glob("plugins/*/skills/*/")):
        lib = skill.parent.parent / "lib"
        out = dist / f"{skill.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            add_tree(zf, skill, skill.name)
            if lib.is_dir():
                add_tree(zf, lib, f"{skill.name}/lib")
        print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
