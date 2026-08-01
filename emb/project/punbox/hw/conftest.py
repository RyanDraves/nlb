import os
import tempfile

# SKiDL creates its persistent storage directory at import time, which the
# Bazel sandbox forbids; point it at the test's writable temp dir instead.
# (Loaded via conftest so it runs before any test module imports skidl.)
os.environ['XDG_DATA_HOME'] = os.environ.get('TEST_TMPDIR', tempfile.gettempdir())
