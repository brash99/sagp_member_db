"""Compatibility wrapper for the canonical App 2 database builder.

The App 2 builder lives in sagp_db_tools.build_database_from_master.  This
module remains only so older imports do not silently use a divergent contract.
"""

from sagp_db_tools.build_database_from_master import *  # noqa: F401,F403
