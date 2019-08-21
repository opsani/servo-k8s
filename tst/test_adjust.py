#
from helpers import adjust, setcfg

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

def test_adjust(simple_app):
    """test adjust command"""

    setcfg("config_basic.yaml")

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
