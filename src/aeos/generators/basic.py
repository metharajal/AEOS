from pathlib import Path

from aeos.generators.base import write_common_files


def generate(project: Path, name: str) -> list[str]:
    dirs = [
        project / "governance" / "adr",
        project / "governance" / "rfc",
        project / "governance" / "dec",
        project / "governance" / "standards",
        project / "governance" / "playbooks",
        project / "docs",
        project / "src",
        project / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True)

    write_common_files(project, name)

    return [
        f"{name}/",
        f"{name}/README.md",
        f"{name}/aeos.toml",
        f"{name}/.gitignore",
        f"{name}/governance/",
        f"{name}/docs/",
        f"{name}/src/",
        f"{name}/tests/",
    ]
