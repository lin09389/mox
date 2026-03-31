import re
import sys
import warnings


def _is_pytest_process() -> bool:
    command_line = " ".join(sys.argv).lower()
    return bool(re.search(r"\bpytest\b", command_line))


if _is_pytest_process():
    warnings.filterwarnings(
        "ignore",
        message=r"urllib3 .* doesn't match a supported version!",
        category=Warning,
    )
    warnings.filterwarnings(
        "ignore",
        message=r"builtin type SwigPyPacked has no __module__ attribute",
        category=DeprecationWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=r"builtin type SwigPyObject has no __module__ attribute",
        category=DeprecationWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=r"builtin type swigvarlink has no __module__ attribute",
        category=DeprecationWarning,
    )
