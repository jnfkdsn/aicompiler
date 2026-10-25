"""Write C++ text for this lesson's one integer-addition function."""
from pathlib import Path
import sys

name = Path(sys.argv[1]).read_text().strip()
if name not in {"add", "sum"}:
    raise SystemExit("This example accepts only add or sum.")
output = Path(sys.argv[2])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("""#ifdef SELECT_DECLARATIONS
#undef SELECT_DECLARATIONS
int @NAME@(int a, int b);
#endif

#ifdef SELECT_DEFINITIONS
#undef SELECT_DEFINITIONS
int @NAME@(int a, int b) {
  return a + b;
}
#endif
""".replace("@NAME@", name))
