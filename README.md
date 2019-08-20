# servo-k8s
Optune servo driver for Kubernetes (native)

This driver supports an application deployed on k8s, as a number of **Deployment** objects in a single namespace. The namespace name is the application name and all Deployment objects in that namespace are considered part of the application.

This driver requires the `adjust.py` module from `git@github.com:opsani/servo.git`. Place a copy of the file in the same directory as the `adjust` executable found here.

>If the `OPTUNE_USE_DEFAULT_NAMESPACE` environment variable is set, the driver uses the default namespace rather than the application name. This is useful when the servo/driver runs in a pod in the same namespace as the application (i.e., the servo is embedded in the application)

Each container in the application's pods is considered a separate component. The component names are reported by 'adjust --query' as follows:
- if the deployment's pod template has a single container, the component name is the deployment object's name.
- if the pod template has multiple containers, each one is a component named ${deployment}/${container}

For each component of the application, the following settings are automatically available when 'adjust --query' is ran:
replicas, mem, cpu (pending: add support for mem\_limit, mem\_request, cpu\_limit, cpu\_request).
If a configuration file is present at ./config.yaml, any custom component settings in it are also returned by 'adjust --query' and map to environment variables of the matching container.  In this file, if present, the k8s adjust driver configuration is under the _k8s_ top level key, while any environment variable settings are under a secondary key _application_ in the same formate as as the expected output of 'adjust --query'. Note this file should not include the pre-defined settings noted above - if you have environment variables with the same name, they cannot be set by this driver.

Example `config.yaml` configuration file:

    k8s:
       whitelist_deployment_names:  [ "httpd" ]
       application:
          components:
             httpd:
                settings:
                   workers:
                      type: linear
                      min: 1
                      max: 20
                      step: 1
                      value: 1

This adds a new setting `workers` to the pod named `httpd`; note that the container spec in the pod manifest should include `env: [ {name: workers, value : N} ]`. Only env settings that have a `value` key are supported, if the container has settings with `valueFrom`, these should NOT be listed in the configuration file.

To exclude a deployment from tuning, set `optune.ai/exclude` label to `'1'`. If including the servo in the application namespace, ensure this label is set on its Deployment object.

To work with _only_ an explicit list of valid deployments within the target namespace, include a list of these deployment names in the config.yaml file under the `whitelist_deployment_names` key, as shown in the example above.  If this list is present in the config file, then only matching deployments will be tuned.

Limitations:
- works only on 'deployment' objects, other types of controllers are not supported.
- minimal tested k8s server version: 1.8.
- if memory or CPU resource limit/request is not set, its value is returned as 0.
- each container in a pod is treated as a separate 'component', however the replicas setting cannot be controlled individually for the containers in the same pod. If 'replicas' is set for multi-container pods and the values are different for the different containers, the last one prevails and will be applied to the pod (and thus to all its containers).

## Running the tests

To run the tests, get a copy of the opsani/servo-k8s repo on a host that has `minikube` installed and running. There should be no deployments in the default namespace (verify this by running `kubectl get deployment`). A copy or symlink to the `adjust.py` module from the opsani/servo repo is also required. The tests use `pytest` to run.

Example setup:

```
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
