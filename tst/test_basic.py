import pytest

import subprocess

from helpers import adjust, setcfg

# NOTE: all tests depending on 'simple_app' do not modify the app
# (app-modifying tests should be in separate modules, to get a new copy of the app)

def test_cfgerr():
    # print(os.getcwd(), request.config.rootdir, __file__, file=open("/tmp/ttt","w"))
    setcfg("config_syntaxerr.yaml")
    exit_code, data = adjust("--describe", "default")
    assert exit_code != 0
    assert data["status"] == "failed"
    assert data["reason"] == "unknown" # we don't have a special code for config errors

def test_init(simple_app):
    """test simple initial setup, with a 'reference' app that has config identical to the 'active' app"""

    setcfg("config_basic.yaml")

    exit_code, data = adjust("--describe", "default")
    assert exit_code == 0
    assert data and isinstance(data, dict)

    # check expected result (single component)
    assert len(data["application"]["components"]) == 1

    # check the 'monitoring' data, spec and version should be the same for the active and reference app
    mon = data["monitoring"] # must be present
    assert mon["spec_id"] == mon["ref_spec_id"]
    assert mon["version_id"] == mon["ref_version_id"]
    assert mon["runtime_id"] != mon["ref_runtime_id"] # should be different (hashes of pod UIDs)

def test_info(simple_app):
    """test info command"""

    exit_code, data = adjust("--info")
    assert data["version"] # should be present and not empty

# FAIL: driver returns seemingly normal data, even if app is not present at all (data is from defaults in the config file)
#@pytest.mark.skipif(True, reason="BUG")
def test_noapp(simple_app):
    setcfg("config_single.yaml")
    exit_code, data = adjust("--describe", "not-here")
    assert exit_code != 0
    assert data and isinstance(data, dict)
    # TBD: status/reason tests
    assert data["status"] == "aborted"
    assert data["reason"] == "app-unavailable" # FIXME, not a documented 'reason' code
