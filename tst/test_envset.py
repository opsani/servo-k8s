import pytest

import helpers
from helpers import adjust, setcfg

@pytest.fixture(scope="function")
def envapp():
    """set up a simple app for tests. Setup is with scope=module, therefore tests that modify the app should be in a separate file, to get cleaned up and not affect other tests"""
    helpers.silent("kubectl delete -f dep-n179.yaml")
    helpers.silent("kubectl delete -f dep-n179-ref.yaml")
    helpers.run("kubectl apply -f dep-env.yaml")

def test_envset(envapp):
    setcfg("config_env.yaml")

    exit_code, data = adjust("--describe", "default")
    assert exit_code == 0
    assert data and isinstance(data, dict)

    assert len(data["application"]["components"]) == 1
    settings = data["application"]["components"]["nginx-deployment"]["settings"]
    assert settings["EVAR"]["value"] == 11 # initial value in config

    # modify env with a manual patch command
    helpers.run("kubectl apply -f dep-env2.yaml")
    helpers.run("kubectl rollout status deployment nginx-deployment")

    exit_code, data = adjust("--describe", "default")
    assert exit_code == 0
    assert data and isinstance(data, dict)

    settings = data["application"]["components"]["nginx-deployment"]["settings"]
    assert settings["EVAR"]["value"] == 22 # updated from kubectl apply
