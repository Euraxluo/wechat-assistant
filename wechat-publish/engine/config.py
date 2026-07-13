"""运行配置加载：每次发布只写 runs/<slug>.json，不改编译器。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = PROJECT_DIR / "runs"
TOPICS_DIR = PROJECT_DIR / "config" / "topics"


@dataclass
class PublishConfig:
    """单次发布的全部参数。"""

    topic: str
    slug: str
    title: str
    author: str
    digest: str
    html: str
    cover: str
    images_dir: str | None = None

    @property
    def html_path(self) -> Path:
        return _resolve(self.html)

    @property
    def cover_path(self) -> Path:
        return _resolve(self.cover)

    @property
    def images_dir_path(self) -> Path | None:
        if not self.images_dir:
            return None
        return _resolve(self.images_dir)

    def validate(self) -> None:
        if not self.html_path.exists():
            raise FileNotFoundError(f"正文 HTML 不存在: {self.html_path}")
        if not self.cover_path.exists():
            raise FileNotFoundError(f"封面图不存在: {self.cover_path}")
        if self.images_dir_path and not self.images_dir_path.is_dir():
            raise FileNotFoundError(f"图片目录不存在: {self.images_dir_path}")


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_DIR / p


def load_run_config(run_path: str | Path) -> PublishConfig:
    """从 runs/*.json 加载配置。"""
    path = Path(run_path)
    if not path.is_absolute():
        path = RUNS_DIR / path if path.parent == Path(".") else PROJECT_DIR / path
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = PublishConfig(
        topic=data["topic"],
        slug=data.get("slug", path.stem),
        title=data["title"],
        author=data.get("author", "AI提效实验室"),
        digest=data["digest"],
        html=data["html"],
        cover=data["cover"],
        images_dir=data.get("images_dir"),
    )
    cfg.validate()
    return cfg


def topic_profile_path(topic: str) -> Path:
    return TOPICS_DIR / f"{topic}.md"
