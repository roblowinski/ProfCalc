import pathlib
import re


def test_no_broad_except_exception_in_src():
    """Fail if any source file in src/profcalc contains a bare
    `except Exception` clause. This prevents re-introducing broad catches.
    """
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    src_dir = repo_root.joinpath("src", "profcalc")
    pattern = re.compile(r"^\s*except\s+Exception\b")
    offenders = []
    for p in src_dir.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                offenders.append(f"{p.relative_to(repo_root)}:{i}: {line.strip()}")

    if offenders:
        msg = "Found broad except Exception clauses in source files:\n" + "\n".join(offenders)
        raise AssertionError(msg)
