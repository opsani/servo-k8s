from helpers import setup_deployment, cleanup_deployment, query_dep, adjust_dep


def test_query_env_var_setting():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-query-env-var-setting
    spec:
      selector:
        matchLabels:
          app: test-query-env-var-setting
      template:
        metadata:
          labels:
            app: test-query-env-var-setting
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: everything
    """
    cfg = """
    k8s:
      application:
        components:
          test-query-env-var-setting:
            env:
              ANYTHING:
                values:
                  - everything
                  - nothing
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-query-env-var-setting']['settings']['ANYTHING']
            ['value'] == 'everything')
    cleanup_deployment(dep)


def test_query_env_var_setting_with_default_value():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-query-env-var-setting-with-default-value
    spec:
      selector:
        matchLabels:
          app: test-query-env-var-setting-with-default-value
      template:
        metadata:
          labels:
            app: test-query-env-var-setting-with-default-value
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
    """
    cfg = """
    k8s:
      application:
        components:
          test-query-env-var-setting-with-default-value:
            env:
              ANYTHING:
                default: nothing
                values:
                  - everything
                  - nothing
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-query-env-var-setting-with-default-value']['settings']['ANYTHING']
            ['value'] == 'nothing')
    cleanup_deployment(dep)


def test_adjust_env_var_setting():
    dep = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: test-adjust-env-var-setting
    spec:
      selector:
        matchLabels:
          app: test-adjust-env-var-setting
      template:
        metadata:
          labels:
            app: test-adjust-env-var-setting
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: everything
    """
    cfg = """
    k8s:
      application:
        components:
          test-adjust-env-var-setting:
            env:
              ANYTHING:
                values:
                  - everything
                  - nothing
    """
    setup_deployment(dep)
    adjust_dep(cfg, {'application': {
        'components': {'test-adjust-env-var-setting': {'settings': {'ANYTHING': {'value': 'nothing'}}}}}})
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-adjust-env-var-setting']['settings']['ANYTHING']
            ['value'] == 'nothing')
    cleanup_deployment(dep)
