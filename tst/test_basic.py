# import pytest

import subprocess

from helpers import adjust, setcfg

def test_cfgerr():
    # print(os.getcwd(), request.config.rootdir, __file__, file=open("/tmp/ttt","w"))
    setcfg("config_syntaxerr.yaml")
    exit_code, data = adjust("--describe", "default")
    assert exit_code != 0
    assert data["status"] == "failed"
    assert data["reason"] == "unknown" # we don't have a special code for config errors

def run(cmd):
    """basic execution of a command, stdout and stderr are not redirected (end up in py.test logs), raise exception on errors"""
    subprocess.run(cmd, shell=True, check=True)

def silent(cmd):
    """run a command and ignore stdout/stderr and non-zero exit status"""
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

def appsetup():
    silent("kubectl delete -f dep-n179.yaml")
    silent("kubectl delete -f dep-n179-ref.yaml")
    run("kubectl apply -f dep-n179.yaml")
    run("kubectl apply -f dep-n179-ref.yaml")

def test_init():
    """test simple initial setup, with a 'reference' app that has config identical to the 'active' app"""

    setcfg("config_basic.yaml")
    appsetup()

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

rep2 = {
  "state": {
    "application": {
      "components": {
        "nginx-deployment": {
           "settings": {"replicas" : {"value": 2}}
        }
      }
    }
  },
  "control" : {"timeout":30}
}

def test_adjust():
    """test adjust command"""

    setcfg("config_basic.yaml")
    appsetup()

    exit_code, data = adjust("--describe", "default")
    assert exit_code == 0
    assert data and isinstance(data, dict)

    # check expected result (single component)
    assert len(data["application"]["components"]) == 1

    # save the initial 'monitoring' data
    mon = data["monitoring"] # must be present

    # run adjust (changes replicas to 2 from the initial 3)
    exit_code, data = adjust("default", stdin=rep2)

    mon2 = data["monitoring"]

    # spec & version should not be affected by the adjust, nor ref app run ID
    assert mon["spec_id"] == mon2["spec_id"]
    assert mon["version_id"] == mon2["version_id"]
    assert mon["ref_spec_id"] == mon2["ref_spec_id"]
    assert mon["ref_version_id"] == mon2["ref_version_id"]
    assert mon["ref_runtime_id"] == mon2["ref_runtime_id"]

    # however, run id should change (different number of replicas)
    assert mon["runtime_id"] != mon2["runtime_id"]

    # check again with 'describe'
    exit_code, data = adjust("--describe", "default")

    mon2 = data["monitoring"]

    # spec & version should not be affected by the adjust
    assert mon["spec_id"] == mon2["spec_id"]
    assert mon["version_id"] == mon2["version_id"]
    assert mon["ref_spec_id"] == mon2["ref_spec_id"]
    assert mon["ref_version_id"] == mon2["ref_version_id"]
