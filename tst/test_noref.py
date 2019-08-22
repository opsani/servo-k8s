import pytest

from helpers import adjust, setcfg
import helpers

def test_no_refapp(simple_app):
    setcfg("config_basic.yaml")
    # delete the 'reference app'
    helpers.silent("kubectl delete -f dep-n179-ref.yaml")
    exit_code, data = adjust("--describe", "not-here")
    print("test_no_refapp", data)
    assert exit_code != 0
    assert data["status"] == "aborted"
    assert data["reason"] == "ref-app-unavailable"
