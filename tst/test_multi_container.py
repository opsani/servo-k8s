from helpers import setup_deployment, cleanup_deployment, query_dep, adjust_dep


def test_query_default_container():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-query-default-container
    spec:
      selector:
        matchLabels:
          app: test-query-default-container
      template:
        metadata:
          labels:
            app: test-query-default-container
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: everything
            - name: collateral
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: nothing
    """
    cfg = """
    k8s:
      application:
        components:
          test-query-default-container:
            env:
              ANYTHING:
                values:
                  - everything
                  - nothing
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-query-default-container']['settings']['ANYTHING']
            ['value'] == 'everything')
    cleanup_deployment(dep)


def test_adjust_default_container():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-adjust-default-container
    spec:
      selector:
        matchLabels:
          app: test-adjust-default-container
      template:
        metadata:
          labels:
            app: test-adjust-default-container
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: everything
            - name: collateral
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: nothing
    """
    cfg = """
    k8s:
      application:
        components:
          test-adjust-default-container:
            env:
              ANYTHING:
                values:
                  - everything
                  - nothing
    """
    setup_deployment(dep)
    adjust_dep(cfg, {'application': {
        'components': {'test-adjust-default-container': {'settings': {'ANYTHING': {'value': 'nothing'}}}}}})
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-adjust-default-container']['settings']['ANYTHING']
            ['value'] == 'nothing')
    cleanup_deployment(dep)


def test_query_specific_container():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-query-specific-container
    spec:
      selector:
        matchLabels:
          app: test-query-specific-container
      template:
        metadata:
          labels:
            app: test-query-specific-container
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: everything
            - name: collateral
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: nothing
    """
    cfg = """
    k8s:
      application:
        components:
          test-query-specific-container/collateral:
            env:
              ANYTHING:
                values:
                  - everything
                  - nothing
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-query-specific-container/collateral']['settings']['ANYTHING']
            ['value'] == 'nothing')
    cleanup_deployment(dep)


def test_adjust_specific_container():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-adjust-specific-container
    spec:
      selector:
        matchLabels:
          app: test-adjust-specific-container
      template:
        metadata:
          labels:
            app: test-adjust-specific-container
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: everything
            - name: collateral
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: ANYTHING
                  value: nothing
    """
    cfg = """
    k8s:
      application:
        components:
          test-adjust-specific-container/collateral:
            env:
              ANYTHING:
                values:
                  - everything
                  - nothing
    """
    setup_deployment(dep)
    adjust_dep(cfg, {'application': {
        'components': {
            'test-adjust-specific-container/collateral': {'settings': {'ANYTHING': {'value': 'everything'}}}}}})
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-adjust-specific-container/collateral']['settings']['ANYTHING']
            ['value'] == 'everything')
    cleanup_deployment(dep)
