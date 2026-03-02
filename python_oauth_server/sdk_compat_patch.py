"""
SDK Compatibility Patch
-----------------------
Authlete Python SDK v1.3.0 (PyPI) ships an incomplete `GrantManagementAction`
enum that is missing entries added in later versions of the Authlete V3 API:

    Missing: NO_CONTENT, NOT_FOUND, INTERNAL_SERVER_ERROR

When the Authlete backend returns one of these action values,
`authlete/types/jsonable.py` (line 64) does:

    attrType[value]  # e.g. GrantManagementAction['NO_CONTENT']

...which raises `KeyError`, crashing the ASGI worker with a 500 and causing
the client connection to drop with "Server disconnected without sending a response."

This module monkey-patches the installed enum class to inject the missing
values before any endpoint module imports it.

TODO: Remove this patch once the upstream `authlete-python` package is updated
      to include these enum members (tracked: authlete/authlete-python on GitHub).
"""

import logging
from enum import auto

logger = logging.getLogger(__name__)


def _patch_grant_management_action():
    from authlete.dto.grant_management_action import GrantManagementAction

    missing = {
        'NO_CONTENT':           auto(),
        'NOT_FOUND':            auto(),
        # 'INTERNAL_SERVER_ERROR': auto(),
    }

    existing_names = {e.name for e in GrantManagementAction}
    patched = []

    for name, value in missing.items():
        if name not in existing_names:
            # Extended the enum by adding a new member directly to its _member_map_
            # and _value2member_map_ — the standard approach for runtime enum patching.
            new_member = object.__new__(GrantManagementAction)
            new_member._name_ = name
            new_member._value_ = len(GrantManagementAction) + 1
            GrantManagementAction._member_map_[name] = new_member
            GrantManagementAction._value2member_map_[new_member._value_] = new_member
            GrantManagementAction._member_names_.append(name)
            patched.append(name)

    if patched:
        logger.warning(
            "SDK COMPAT PATCH applied: Injected missing GrantManagementAction "
            "enum members into authlete v1.3.0: %s. "
            "Remove this patch once upstream SDK is updated.",
            patched
        )
    else:
        logger.debug("SDK COMPAT PATCH: GrantManagementAction already complete, no patch needed.")


def apply_all():
    _patch_grant_management_action()
