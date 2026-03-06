"""
Verification script for COBIT 2019 seed data.

Run this after seeds/cobit_2019.py to confirm everything loaded correctly:
    python -m seeds.verify_cobit

Prints a summary of what's in the database and flags any obvious problems.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.store import KnowledgeStore


def verify_cobit_2019() -> None:
    """
    Query the database and confirm COBIT 2019 loaded as expected.
    Prints pass/fail for each check.
    """
    store = KnowledgeStore()
    errors: list[str] = []

    print("Verifying COBIT 2019 seed data...\n")

    # Check 1: Framework exists
    framework = store.get_framework_by_slug("cobit_2019")
    if not framework:
        print("FAIL: Framework 'cobit_2019' not found in database.")
        print("      Did the seed script run successfully?")
        return

    print(f"PASS: Framework found — {framework.name} (id: {framework.id})")

    # Check 2: All 5 domains exist
    domains = store.get_domains_by_framework(framework.id)
    expected_domains = {"EDM", "APO", "BAI", "DSS", "MEA"}
    found_domains = {d.code for d in domains}

    if found_domains == expected_domains:
        print(f"PASS: All 5 domains found — {', '.join(sorted(found_domains))}")
    else:
        missing = expected_domains - found_domains
        extra = found_domains - expected_domains
        if missing:
            errors.append(f"Missing domains: {missing}")
            print(f"FAIL: Missing domains: {missing}")
        if extra:
            errors.append(f"Unexpected domains: {extra}")
            print(f"WARN: Unexpected domains found: {extra}")

    # Check 3: Control counts per domain
    expected_counts = {
        "EDM": 5,
        "APO": 14,
        "BAI": 11,
        "DSS": 6,
        "MEA": 4,
    }

    print()
    print("Control counts per domain:")
    total_controls = 0

    for domain in sorted(domains, key=lambda d: d.code):
        controls = store.get_controls_by_domain(domain.id)
        actual = len(controls)
        expected = expected_counts.get(domain.code, "?")
        total_controls += actual

        status = "PASS" if actual == expected else "FAIL"
        print(f"  {status}: {domain.code} — {actual} controls (expected {expected})")

        if actual != expected:
            errors.append(f"{domain.code}: expected {expected}, got {actual}")

        # Print control IDs for inspection
        codes = sorted(c.control_id_code for c in controls)
        print(f"         {', '.join(codes)}")

    print()
    print(f"Total controls: {total_controls} (expected 40)")
    if total_controls != 40:
        errors.append(f"Total controls: expected 40, got {total_controls}")

    # Check 4: Spot-check a few specific controls exist
    print()
    print("Spot-checking specific controls:")

    spot_checks = [
        ("EDM01", "Ensured Governance Framework Setting and Maintenance"),
        ("APO12", "Managed Risk"),
        ("BAI06", "Managed IT Changes"),
        ("DSS05", "Managed Security Services"),
        ("MEA03", "Managed Compliance with External Requirements"),
    ]

    for code, expected_title in spot_checks:
        control = store.get_control_by_code("cobit_2019", code)
        if not control:
            print(f"  FAIL: {code} not found")
            errors.append(f"Control {code} not found")
        elif control.title != expected_title:
            print(f"  WARN: {code} found but title differs")
            print(f"        Expected: {expected_title}")
            print(f"        Got:      {control.title}")
        else:
            print(f"  PASS: {code} — {control.title}")

    # Summary
    print()
    if not errors:
        print("All checks passed. COBIT 2019 seed data looks good.")
        print("Ready to proceed to ISO 27001 seeding.")
    else:
        print(f"{len(errors)} check(s) failed:")
        for e in errors:
            print(f"  - {e}")
        print("\nFix the issues above before proceeding.")


if __name__ == "__main__":
    verify_cobit_2019()
