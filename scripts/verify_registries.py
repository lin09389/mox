#!/usr/bin/env python3
"""CI health-check: verify all attack and defense modules loaded successfully.

Exit code 0  = all OK
Exit code 1  = one or more modules failed to load
"""

import sys

# Ensure the mox package is importable (run from repo root with `python -m scripts.verify_registries`)
from mox.attacks import verify_registry as verify_attacks, ATTACK_REGISTRY
from mox.defense import verify_registry as verify_defenses, DEFENSE_REGISTRY

failures: list[str] = []


attack_fails = verify_attacks()
if attack_fails:
    failures.append(f"Attack modules failed: {attack_fails}")
else:
    print(f"  Attacks:  {len(ATTACK_REGISTRY.registered_names)} registered OK")

defense_fails = verify_defenses()
if defense_fails:
    failures.append(f"Defense modules failed: {defense_fails}")
else:
    print(f"  Defenses: {len(DEFENSE_REGISTRY.registered_names)} registered OK")


if failures:
    print("\nFAILED:")
    for msg in failures:
        print(f"  - {msg}")
    sys.exit(1)
else:
    print("\nAll registries healthy.")
    sys.exit(0)
