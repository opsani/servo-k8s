# servo-k8s
Optune servo driver for Kubernetes (native)

This driver supports an application deployed on K8s, as a number of **Deployment** objects, and optionally specific **Containers**, in a single namespace. The namespace name is the application name and all **Deployment** objects in that namespace are considered part of the application.

> If the `OPTUNE_USE_DEFAULT_NAMESPACE` environment variable is set, the driver uses the default namespace rather than the application name. This is useful when the driver runs in a deployment in the same namespace as the application (i.e., the servo is embedded in the application).

This driver requires a configuration file to be present and to have deployments (and optionally their particular containers) specified as component names. That way the driver will know which deployments to operate on.

The component name should be either of these two formats `deploymentName` or `deploymentName/containerName`. `deploymentName` and optionally `containerName` should reflect names of the deployment and the container that you want to optimize in your cluster. In case you specify just `deploymentName` in a name of a component, only the first container from a list of containers from a result of a command `kubectl get deployment/deploymentName -o json` will be used. 

You can tune arbitrary environment variables by defining them in a section `env` which is on the same level as section `settings` as can be seen in the example below. For environment variables we support only `range` and `enum` setting types. For `range` available setting properties are `min`, `max`, `step` and `unit`. For `enum` available setting properties are `values` and `unit`. Setting properties `min`, `max` and `step` denote respective boundaries of optimization for a particular setting. For example, `min: 1, max: 6, step: .125` for setting `mem` would mean the optimization will lie in a range of `1 GiB` to `6 GiB` with a step of change of at least `128 MiB`, but can be multiple of that.

In case you don't have environment variable already set in a Deployment object manifest for a first container in case your component name is just `deploymentName` or for a particular container in case you explicitly specified it's name in a component name like this `deploymentName/containerName`, you can define a setting property `default` with the default value for that particular environment variable. The `default` value will be used at the time of a first adjustment in case no previous value was found. 

Only environment variables with a key `value` are supported. We do not support environment variables that have `valueFrom` value-defining property. Those without `value` should not be listed in section `env`.

Example `config.yaml` configuration file:

    k8s:
       application:
          components:
             nginx/frontend:
                settings:
                    cpu:
                        min: .1
                        max: 2
                        step: .1
                    mem:
                        min: .5
                        max: 8
                        step: .1
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

To exclude a deployment from tuning, set `optune.ai/exclude` label to `'1'`. If you include the driver in the application namespace, please make sure you define this label in driver's Deployment object.

Limitations:
- works only on `deployment` objects, other types of controllers are not supported.
- each container in a Deployment is treated as a separate `component`, however, the `replicas` setting cannot be controlled individually for the containers in the same deployment. If `replicas` is set for multi-container deployment and the values are different for different containers, the resulting adjustment becomes unpredictable. Please, define only one `replicas` setting per component-deployment.

## Test requrements

`tst/test_encoders.py` requires `base.py` and `jvm.py` to be present in `encoders/` in the root directory. `base.py` can be downloaded from https://github.com/opsani/servo/tree/master/encoders. `jvm.py` can be downloaded from https://github.com/opsani/encoder-jvm/tree/master/encoders.
