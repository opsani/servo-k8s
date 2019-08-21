from helpers import setup_deployment, cleanup_deployment, query_dep, adjust_dep


def test_encoder_query_env_var():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-encoder-query-env-var
    spec:
      selector:
        matchLabels:
          app: test-encoder-query-env-var
      template:
        metadata:
          labels:
            app: test-encoder-query-env-var
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: JAVA_OPTS
                  value: -XX:GCTimeRatio=69
    """
    cfg = """
    k8s:
      application:
        components:
          test-encoder-query-env-var:
            env:
              JAVA_OPTS:
                encoder:
                  name: jvm
                  settings:
                    GCTimeRatio:
                      min: 9
                      max: 99
                      step: 10
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert desc['application']['components']['test-encoder-query-env-var']['settings']['GCTimeRatio']['value'] == 69
    cleanup_deployment(dep)


def test_encoder_adjust_env_var():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-encoder-adjust-env-var
    spec:
      selector:
        matchLabels:
          app: test-encoder-adjust-env-var
      template:
        metadata:
          labels:
            app: test-encoder-adjust-env-var
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600"]
              env:
                - name: JAVA_OPTS
                  value: -XX:GCTimeRatio=69
    """
    cfg = """
    k8s:
      application:
        components:
          test-encoder-adjust-env-var:
            env:
              JAVA_OPTS:
                encoder:
                  name: jvm
                  settings:
                    GCTimeRatio:
                      min: 9
                      max: 99
                      step: 10
    """
    setup_deployment(dep)
    adjust_dep(cfg, {'application': {
        'components': {'test-encoder-adjust-env-var': {'settings': {'GCTimeRatio': {'value': 19}}}}}})
    desc = query_dep(cfg)
    assert desc['application']['components']['test-encoder-adjust-env-var']['settings']['GCTimeRatio']['value'] == 19
    cleanup_deployment(dep)


def test_encoder_query_command():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-encoder-query-command
    spec:
      selector:
        matchLabels:
          app: test-encoder-query-command
      template:
        metadata:
          labels:
            app: test-encoder-query-command
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600", "&&", "echo", "-XX:GCTimeRatio=69"]
    """
    cfg = """
    k8s:
      application:
        components:
          test-encoder-query-command:
            command:
              encoder:
                name: jvm
                before:
                  - /bin/sh
                  - -c
                  - sleep 3600
                  - "&&"
                  - echo
                settings:
                  GCTimeRatio:
                    min: 9
                    max: 99
                    step: 10
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert desc['application']['components']['test-encoder-query-command']['settings']['GCTimeRatio']['value'] == 69
    cleanup_deployment(dep)


def test_encoder_adjust_command():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-encoder-adjust-command
    spec:
      selector:
        matchLabels:
          app: test-encoder-adjust-command
      template:
        metadata:
          labels:
            app: test-encoder-adjust-command
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600", "&&", "echo", "-XX:GCTimeRatio=69"]
    """
    cfg = """
    k8s:
      application:
        components:
          test-encoder-adjust-command:
            command:
              encoder:
                name: jvm
                before:
                  - /bin/sh
                  - -c
                  - sleep 3600
                  - "&&"
                  - echo
                settings:
                  GCTimeRatio:
                    min: 9
                    max: 99
                    step: 10
    """
    setup_deployment(dep)
    adjust_dep(cfg, {'application': {
        'components': {'test-encoder-adjust-command': {'settings': {'GCTimeRatio': {'value': 19}}}}}})
    desc = query_dep(cfg)
    assert desc['application']['components']['test-encoder-adjust-command']['settings']['GCTimeRatio']['value'] == 19
    cleanup_deployment(dep)


def test_encoder_query_with_setting_prefix():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-encoder-query-with-setting-prefix
    spec:
      selector:
        matchLabels:
          app: test-encoder-query-with-setting-prefix
      template:
        metadata:
          labels:
            app: test-encoder-query-with-setting-prefix
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600", "&&", "echo", "-XX:GCTimeRatio=69"]
              env:
                - name: JAVA_OPTS
                  value: -XX:GCTimeRatio=69
    """
    cfg = """
    k8s:
      application:
        components:
          test-encoder-query-with-setting-prefix:
            command:
              encoder:
                name: jvm
                before:
                  - /bin/sh
                  - -c
                  - sleep 3600
                  - "&&"
                  - echo
                setting_prefix: cmd-
                settings:
                  GCTimeRatio:
                    min: 9
                    max: 99
                    step: 10
            env:
              JAVA_OPTS:
                encoder:
                  name: jvm
                  setting_prefix: env-
                  settings:
                    GCTimeRatio:
                      min: 9
                      max: 99
                      step: 10
    """
    setup_deployment(dep)
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-encoder-query-with-setting-prefix']['settings']['cmd-GCTimeRatio']
            ['value'] == 69)
    assert (desc['application']['components']['test-encoder-query-with-setting-prefix']['settings']['env-GCTimeRatio']
            ['value'] == 69)
    cleanup_deployment(dep)


def test_encoder_adjust_with_setting_prefix():
    dep = """
    apiVersion: extensions/v1beta1
    kind: Deployment
    metadata:
      name: test-encoder-adjust-with-setting-prefix
    spec:
      selector:
        matchLabels:
          app: test-encoder-adjust-with-setting-prefix
      template:
        metadata:
          labels:
            app: test-encoder-adjust-with-setting-prefix
        spec:
          containers:
            - name: main
              image: alpine:latest
              command: ["/bin/sh", "-c", "sleep 3600", "&&", "echo", "-XX:GCTimeRatio=69"]
              env:
                - name: JAVA_OPTS
                  value: -XX:GCTimeRatio=69
    """
    cfg = """
    k8s:
      application:
        components:
          test-encoder-adjust-with-setting-prefix:
            command:
              encoder:
                name: jvm
                before:
                  - /bin/sh
                  - -c
                  - sleep 3600
                  - "&&"
                  - echo
                setting_prefix: cmd-
                settings:
                  GCTimeRatio:
                    min: 9
                    max: 99
                    step: 10
            env:
              JAVA_OPTS:
                encoder:
                  name: jvm
                  setting_prefix: env-
                  settings:
                    GCTimeRatio:
                      min: 9
                      max: 99
                      step: 10
    """
    setup_deployment(dep)
    adjust_dep(cfg, {'application': {
        'components': {'test-encoder-adjust-with-setting-prefix': {
            'settings': {'cmd-GCTimeRatio': {'value': 19}, 'env-GCTimeRatio': {'value': 19}}}}}})
    desc = query_dep(cfg)
    assert (desc['application']['components']['test-encoder-adjust-with-setting-prefix']['settings']['cmd-GCTimeRatio']
            ['value'] == 19)
    assert (desc['application']['components']['test-encoder-adjust-with-setting-prefix']['settings']['env-GCTimeRatio']
            ['value'] == 19)
    cleanup_deployment(dep)
