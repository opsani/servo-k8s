import pytest

from helpers import adjust, setcfg
import helpers

# FAIL: missing 'reference app' isn't detected
@pytest.mark.skipif(True, reason="BUG")
def test_no_refapp(simple_app):
    setcfg("config_basic.yaml")
    # delete the 'reference app'
    helpers.silent("kubectl delete -f dep-n179-ref.yaml")
    exit_code, data = adjust("--describe", "not-here")
    print("test_no_refapp", data)
    assert exit_code != 0
    # TODO: shuld get status="aborted", reason="ref-app-unavailable"
