import os

# Settings.openai_api_key has no default, so it must be present before any
# module imports app.config and calls get_settings(). Set it before test
# collection imports anything else.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
