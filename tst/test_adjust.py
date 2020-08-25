#
import requests
from threading import Timer
import time

from helpers import adjust, setcfg, setup_deployment, cleanup_deployment, adjust_dep, run

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

def test_adjust_never_ready():
    """
    The following deployment will never be ready once mem is adjusted to 0.125Gi
    the test verifies adjust ok is not reported in this case
    """
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-adjust-never-ready
    spec:
      selector:
        matchLabels:
          app: test-adjust-never-ready
      strategy:
        rollingUpdate:
          maxSurge: 25%
          maxUnavailable: 25%
        type: RollingUpdate
      template:
        metadata:
          labels:
            app: test-adjust-never-ready
        spec:
          containers:
            - name: main
              image: opsani/co-http
              command:
              - bash
              - -c
              - "if [ $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes) -gt 191058816 ]; then /usr/local/bin/http; else sleep 1d; fi"
              resources:
                requests:
                  cpu: "0.2"
                  memory: "256Mi"
                limits:
                  cpu: "0.2"
                  memory: "256Mi"
              readinessProbe:
                failureThreshold: 1000000
                httpGet:
                  path: /
                  port: 8080
                  scheme: HTTP
                initialDelaySeconds: 30
                periodSeconds: 10
                successThreshold: 1
                timeoutSeconds: 5
    """
    cfg = """
    k8s:
      application:
        components:
          test-adjust-never-ready:
            settings:
              mem:
                min: .125
                max: .5
                step: .125
    """
    setup_deployment(dep)
    captured_error = None
    try:
      adjust_dep(cfg, {'control': { 'timeout': 90 }, 'application': {'components': {'test-adjust-never-ready': {'settings': {'mem': {'value': .125}}}}}})
    except Exception as e:
      captured_error = e

    assert captured_error is not None, 'Adjustment succeeded despite latest revision pods never becoming ready'
    assert 'timed out waiting for replicas to come up' in str(captured_error), 'Adjustment error occurred but did not match the expected error. Error that occured: {}'.format(captured_error)
    assert 'Rollback succeeded' in str(captured_error), 'The expected error occured but rollback failed. Error: {}'.format(captured_error)
    
    cleanup_deployment(dep)

def test_adjust_destroy_new():
    """
    The following deployment will never be ready once mem is adjusted to 0.125Gi
    the test verifies adjust ok is not reported in this case
    """
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-adjust-destroy-new
    spec:
      selector:
        matchLabels:
          app: test-adjust-destroy-new
      strategy:
        rollingUpdate:
          maxSurge: 25%
          maxUnavailable: 25%
        type: RollingUpdate
      template:
        metadata:
          labels:
            app: test-adjust-destroy-new
        spec:
          containers:
            - name: main
              image: opsani/co-http
              command:
              - bash
              - -c
              - "if [ $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes) -gt 191058816 ]; then /usr/local/bin/http; else sleep 1d; fi"
              resources:
                requests:
                  cpu: "0.2"
                  memory: "256Mi"
                limits:
                  cpu: "0.2"
                  memory: "256Mi"
              readinessProbe:
                failureThreshold: 3
                httpGet:
                  path: /
                  port: 8080
                  scheme: HTTP
                initialDelaySeconds: 30
                periodSeconds: 10
                successThreshold: 1
                timeoutSeconds: 5
              livenessProbe:
                failureThreshold: 3
                httpGet:
                  path: /
                  port: 8080
                  scheme: HTTP
                initialDelaySeconds: 30
                periodSeconds: 10
                successThreshold: 1
                timeoutSeconds: 5
    """
    cfg = """
    k8s:
      on_fail: destroy_new
      application:
        components:
          test-adjust-destroy-new:
            settings:
              mem:
                min: .125
                max: .5
                step: .125
    """
    setup_deployment(dep)
    time.sleep(40) # let initial dep become ready before testing url
    run('kubectl expose deployment test-adjust-destroy-new --type=LoadBalancer --port=8080')
    url = run('minikube service test-adjust-destroy-new --url')

    connection_error = None
    def test_url():
      nonlocal connection_error
      try:
        resp = requests.get(url)
      except requests.ConnectionError as e:
        connection_error = 'Test deployment became unreachable: {}'.format(e)
      else:
        if not resp.ok:
          connection_error = 'Test deployment became unreachable, status {}: {}'.format(resp.status_code, resp.text)
      timer = Timer(1, test_url)
      timer.daemon = True
      timer.start()

    timer = Timer(1, test_url)
    timer.daemon = True
    timer.start()

    captured_error = None
    try:
      adjust_dep(cfg, {'application': {'components': {'test-adjust-destroy-new': {'settings': {'mem': {'value': .125}}}}}})
    except Exception as e:
      captured_error = e

    assert captured_error is not None, 'Adjustment succeeded despite latest revision pods never becoming ready'
    assert 'during rollout; component(s) crash restart detected' in str(captured_error), 'Adjustment error occurred but did not match the expected error. Error that occured: {}'.format(captured_error)
    assert 'Rollback succeeded' in str(captured_error), 'The expected error occured but rollback failed. Error: {}'.format(captured_error)

    assert connection_error is None, connection_error
    
    cleanup_deployment(dep)
    run('kubectl delete service test-adjust-destroy-new')
