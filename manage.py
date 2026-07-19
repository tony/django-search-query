#!/usr/bin/env python
"""Django management entry point for the colored-input dev harness.

Runs against :mod:`tests.settings_dev` (in-memory admin site with static files
and browser auto-reload) so ``python manage.py runserver`` shows the colored
search input end to end. It is not part of the published packages.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    """Run a Django management command against the dev settings."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings_dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
