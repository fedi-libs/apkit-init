import shutil
import subprocess
import tempfile
from pathlib import Path

import pathspec


def apply_template(template_url: str, target_dir: Path, context: dict):
    """Clone git repo, handle ignores, and replace variables with .tmpl priority."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Clone
        result = subprocess.run(
            ["git", "clone", "--depth", "1", template_url, tmpdir],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")

        src_root = Path(tmpdir)

        # 2. Handle .apkit-ignores (Previous logic)
        ignore_file = src_root / ".apkit-ignores"
        if ignore_file.exists():
            lines = ignore_file.read_text(encoding="utf-8").splitlines()
            spec = pathspec.PathSpec.from_lines("gitwildmatch", lines)

            to_delete = [
                p
                for p in src_root.rglob("*")
                if spec.match_file(str(p.relative_to(src_root)))
            ]
            for p in to_delete:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                elif p.exists():
                    p.unlink()
            ignore_file.unlink()

        shutil.rmtree(src_root / ".git", ignore_errors=True)

        for src_path in src_root.rglob("*"):
            if src_path.is_dir():
                continue

            rel_path_str = str(src_path.relative_to(src_root))

            is_tmpl = rel_path_str.endswith(".tmpl")

            target_rel_path = rel_path_str
            if is_tmpl:
                target_rel_path = target_rel_path[:-5]

            for k, v in context.items():
                target_rel_path = target_rel_path.replace(f"{{{{{k}}}}}", v)

            dest_path = target_dir / target_rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                content = src_path.read_text(encoding="utf-8")
                for k, v in context.items():
                    content = content.replace(f"{{{{{k}}}}}", v)

                dest_path.write_text(content, encoding="utf-8")

            except UnicodeDecodeError:
                shutil.copy2(src_path, dest_path)
