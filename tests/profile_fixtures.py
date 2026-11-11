"""Minimal test profiles (LABS-1.022): enough schema to test installation and subtype discovery, nothing more."""

from pathlib import Path

from worldmodel.profiles import Profile

HERE = Path(__file__).resolve().parent / "fixtures" / "profiles"

MECHANICAL = Profile("mechanical-fixture", "0.0-test", (str(HERE / "mechanical" / "mechanical.tql"),),
                     vocabulary=(("category", "mechanical-fixture:overhaul", "overhaul"),))
ORGANISATION = Profile("organisation-fixture", "0.0-test", (str(HERE / "organisation" / "organisation.tql"),),
                       slots=(("post-holding", ("class", "context"), "classified"),),
                       vocabulary=(("social-role", "organisation-fixture:site-manager", "site manager"),))
LABORATORY = Profile("laboratory-fixture", "0.0-test", (str(HERE / "laboratory" / "laboratory.tql"),))
ALL = (MECHANICAL, ORGANISATION, LABORATORY)
NEW_TYPES = {"mechanical-fixture": ["maintenance-kind", "part-swap", "scheduled-maintenance-kind"],
             "organisation-fixture": ["acting-post-holding", "company", "post-holding", "staff-member"],
             "laboratory-fixture": ["aliquot", "aliquoting", "core-aliquot", "protocol-step-of", "step-of"]}
