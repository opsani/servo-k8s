# servo-k8s

Optune servo driver for Kubernetes (native)

This driver supports an application deployed on K8s, as a number of **Deployment** objects,
and optionally specific **Containers**, in a single namespace. The namespace name is derived
in one of the following ways:

- If the `OPTUNE_USE_DEFAULT_NAMESPACE` environment variable is set, the driver uses the default
namespace. This is useful when the driver runs in a deployment
in the same namespace as the application (i.e., the servo is embedded in the application).

- If the `OPTUNE_NAMESPACE` environment variable is set, the driver uses the value of said
variable as the namespace.

- If the config (see below) defines a `namespace`, the value defined there will be used

- If none of the above are defined, the `app_id` argument passed into the servo will be used
as the namespace

The precedence of namespace configuration is as follows: `OPTUNE_USE_DEFAULT_NAMESPACE` >
`OPTUNE_NAMESPACE` > configured `namespace` > servo `app_id`. (eg. if `OPTUNE_NAMESPACE` is
set but `OPTUNE_USE_DEFAULT_NAMESPACE` is truthy, the default namespace will be used)

This driver requires the `adjust.py` module from `git@github.com:opsani/servo.git`.
Place a copy of the file in the same directory as the `adjust` executable found here.

This driver also requires a configuration file named `config.yaml` to be present in the same directory as the `adjust`
executable. The file must include a `k8s` configuration dictionary (Note: if the `OPTUNE_USE_DRIVER_NAME` environment
variable is set to a truthy value, the name of the driver file will be used to locate the configuration dictionary instead).
The configuration dictionary must define an `application` dictionary containing a `components` dictionary with the deployments
(and optionally their particular containers) specified as component names. That way the driver will know which
deployments to operate on.

The component name should be either of these two formats `deploymentName` or `deploymentName/containerName`.
The `deploymentName` and optionally `containerName` should reflect names of the deployment and the container
that you want to optimize in your cluster. In case you specify just `deploymentName` in a name of a
component, only the first container from a list of containers from a result of a command
`kubectl get deployment/deploymentName -o json` will be used.

The driver supports tuning of the number of replicas for the deployment as well as the limits and requests for the CPU
and memory resources of the target container. These settings should be specified under the `settings` key for
each desired deployment (see the example below). By default, the container resource requests and limits are both tuned to the same
value. To modify this behaviour, include a `selector` with a value of `request` or `limit`, to exclusively tune the value for `requests`
or `limits` respectively. Additionally, `cpu`, `mem`, and `replicas` settings support pinning
which exempts them from being adjusted by the backend while still reporting their values for the
purpose of measurement.

You can also tune arbitrary environment variables by defining them in a section `env` which is on the same
level as section `settings` as can be seen in the example below. For environment variables we support
only `range` and `enum` setting types. For `range` available setting properties are `min`, `max`,
`step` and `unit`. For `enum` available setting properties are `values` and `unit`. Setting properties
`min`, `max` and `step` denote respective boundaries of optimization for a particular setting.
For example, `min: 1, max: 6, step: .125` for setting `mem` would mean the optimization will lie
in a range of `1 GiB` to `6 GiB` with a step of change of at least `128 MiB`, but can be multiple of that.

In case you don't have environment variable already set in a Deployment object manifest for a first
container in case your component name is just `deploymentName` or for a particular container in
case you explicitly specified it's name in a component name like this `deploymentName/containerName`,
you can define a setting property `default` with the default value for that particular environment
variable. The `default` value will be used at the time of a first adjustment in case no previous value was found.

Only environment variables with a key `value` are supported. We do not support environment variables that
have `valueFrom` value-defining property. Those without `value` should not be listed in section `env`.

The the following optional configurations may also be defined at the same level as the section `application`:

- `adjust_on` - When specified, `adjust_on` should define a python statement to be used as a condition for enabling adjustment. This statement has access
    to the adjustment input in the form of a dictionary named `data`. When the condition evaluates to false, all k8s adjustment
    will be skipped for that adjustment iteration

- `on_fail` - When specified, on fail can be set to one of the following behaviors to be executed in the event of an adjustment failure:
  - `rollback` - (default) Rolls back the failed deployment with `kubectl rollout undo`
  - `destroy` - Scales the failed deployment to 0 replicas with `kubectl patch -p '{ "spec": { "replicas": 0 } }'`
  - `nop` - Take no remedial action

- `settlement` - How much time (in seconds) to wait and monitor target deployments for instability before
considering an adjustment to be successful. Useful for when a pod passes the initial health check but fails some time
afterward.

Example `config.yaml` configuration file:

```yaml
    k8s:
        adjust_on: data["control"]["userdata"]["deploy_to"] == "canary" # Optional, if specified will adjust only if expression is true
        on_fail: rollback # Behavior to enact on a failed adjustment, defaults to rollback. Valid options: 'destroy', 'rollback', and 'nop'
        settlement: 300 # How long to monitor deployments before considering adjustment to be successful
        application:
            components:
                nginx/frontend:
                    settings:
                        cpu:
                            min: .125
                            max: 2
                            step: .125
                        mem:
                            min: .5
                            max: 8
                            step: .125
                            selector: request
                        replicas:
                            min: 3
                            max: 15
                            step: 1
                    env:
                        COMMIT_DELAY:
                            type: range
                            min: 1
                            max: 100
                            step: 1
                            default: 20
                nginx/backend:
                    settings:
                        cpu:
                            pinned: True # Optional
                        mem:
                            pinned: True # Optional
```

To exclude a deployment from tuning, set `optune.ai/exclude` label to `'1'`. If you include the driver in the
application namespace, please make sure you define this label in driver's Deployment object.

Limitations:

- works only on `deployment` objects, other types of controllers are not supported.
- each container in a Deployment is treated as a separate `component`, however,
the `replicas` setting cannot be controlled individually for the containers in the same deployment.
If `replicas` is set for multi-container deployment and the values are different for different containers,
the resulting adjustment becomes unpredictable. Please, define only one `replicas` setting
per component-deployment.

## Required Permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: <TARGET_NAMESPACE>
  name: <ROLE_NAME>
rules:
- apiGroups: ["apps"]
  resources: ["deployments", "PodDisruptionBudget"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["apps"]
  resources: ["replicasets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods", "pods/logs" ,"namespaces"]
  verbs: ["get", "list", "watch" ]
```

## Using an Encoder

Like many other connectors, servo-k8s supports the usage of encoders for language specific settings.
Under the current implementation, encoded settings are injected into the target container via the environment
variable that defines the encoder (such as `JAVA_OPTS` in the example config below). The configuration for the
encoded env has no `type`; it instead specifies an `encoder` dictionary whose key values are `name`, the file name of
the encoder to be invoked (sans the `.py` extension), and `settings`, a dictionary whose values are dependent on the
encoder being used (see encoder documentation for encoder settings config format). For example, a common use case
of the servo-k8s connector is to [encode Java settings](https://github.com/opsani/encoder-jvm) into a `JAVA_OPTS` 
environment variable. Here is an example of such a config:

```yaml
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
```

## Running the tests

The tests are meant to be run by `pytest`. The Python3 version is required, it can be installed with
the OS package manager (see example setup below) or with `python3 -m pip install pytest`.

To run the tests, get a copy of the opsani/servo-k8s repo on a host that has `minikube` installed
and running. There should be no deployments in the default namespace (verify this by running
`kubectl get deployment`). A copy or symlink to the `adjust.py` module from the opsani/servo
repo is also required.

Example setup:

```bash
# this setup assumes Ubuntu 18.4, for earlier versions, please install pip and pytest for Python3 manually, start from
# `https://pip.pypa.io/en/stable/installing/` for setting up pip.
sudo apt-get install -y python3-pytest
cd
git clone git clone git@github.com:opsani/servo
git clone git clone git@github.com:opsani/servo-k8s
cd ~/servo-k8s
ln -s ~/servo/adjust.py . # symlink to the required module

# run the tests
cd tst
py.test-3
```

`tst/test_encoders.py` requires `base.py` and `jvm.py` to be present in `encoders/` in the root directory.
`base.py` can be downloaded from <https://github.com/opsani/servo/tree/master/encoders>. `jvm.py` can be
downloaded from <https://github.com/opsani/encoder-jvm/tree/master/encoders>.
