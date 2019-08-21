import pytest

import subprocess

import helpers

@pytest.fixture(scope="module")
def simple_app():
    """set up a simple app for tests. Setup is with scope=module, therefore tests that modify the app should be in a separate file, to get cleaned up and not affect other tests"""
    helpers.silent("kubectl delete -f dep-n179.yaml")
    helpers.silent("kubectl delete -f dep-n179-ref.yaml")
    helpers.run("kubectl apply -f dep-n179.yaml")
    helpers.run("kubectl apply -f dep-n179-ref.yaml")

