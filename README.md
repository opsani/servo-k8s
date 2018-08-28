# servo-k8s
Optune servo driver for Kubernetes (native)

This driver supports an application deployed on k8s, as a number of **Deployment** objects in a single namespace. The namespace name is the application name and all Deployment objects in that namespace are considered part of the application.

>If the `OPTUNE_USE_DEFAULT_NAMESPACE` environment variable is set, the driver uses the default namespace rather than the application name. This is useful when the servo/driver runs in a pod in the same namespace as the application (i.e., the servo is embedded in the application)

Each container in the application's pods is considered a separate component. The component names are reported by 'adjust --query' as follows:
- if the deployment's pod template has a single container, the component name is the deployment object's name.
- if the pod template has multiple containers, each one is a component named ${deployment}/${container}

For each component of the application, the following settings are automatically available when 'adjust --query' is ran:
replicas, mem, cpu (pending: add support for mem\_limit, mem\_request, cpu\_limit, cpu\_request).
If a configuration file is present at ./app.yaml, any custom component settings in it are also returned by 'adjust --query' and map to environment variables of the matching container. The format of the file, if present, is the same as the expected output of 'adjust --query'. Note it should not include the pre-defined settings noted above - if you have environment variables with the same name, they cannot be set by this driver.

Example `app.yaml` configuration file:

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

Limitations:
- works only on 'deployment' objects, other types of controllers are not supported.
- minimal tested k8s server version: 1.8.
- if memory or CPU resource limit/request is not set, its value is returned as 0.
- each container in a pod is treated as a separate 'component', however the replicas setting cannot be controlled individually for the containers in the same pod. If 'replicas' is set for multi-container pods and the values are different for the different containers, the last one prevails and will be applied to the pod (and thus to all its containers).

