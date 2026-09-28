import os

# Tests must identify themselves explicitly rather than inheriting the
# application's local-development default. Individual tests may still
# override these values when exercising environment-specific behavior.
os.environ.setdefault("DACQUA_ENVIRONMENT", "test")
