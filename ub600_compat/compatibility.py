"""Fail closed outside the single hardware-tested HAOS module build."""

TESTED_KERNEL = "6.18.39-haos"
TESTED_SOURCE_SHA256 = (
    "1396033d5ef1097147214a6fe127c298455a18137fd6d5bb8dbc8bc869b17d20"
)


def require_tested_build(kernel, source_sha256):
    """Do not unload a working stock driver for an untested module build."""
    if kernel != TESTED_KERNEL or source_sha256 != TESTED_SOURCE_SHA256:
        raise ValueError(
            "Untested kernel/module build: stock driver left untouched. "
            "Use an official HAOS update containing native UB600 support, "
            "or wait for a separately validated app release. "
            "There is no force/skip-validation option."
        )
