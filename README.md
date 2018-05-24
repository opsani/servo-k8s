# servo-k8s
Optune servo driver for Kubernetes (native)

This driver supports an application deployed on k8s, as a number of **Deployment** objects in a single namespace. The namespace name is the application name and all Deployment objects in that namespace are considered part of the application.

>If the `OPTUNE_USE_DEFAULT_NAMESPACE` environment variable is set, the driver uses the default namespace rather than the application name. This is useful when the servo/driver runs in a pod in the same namespace as the application (i.e., the servo is embedded in the application)

Each container in the application's pods is considered a separate component. The component names are reported by 'adjust --info' as follows:
- if the deployment's pod template has a single container, the component name is the deployment object's name.
- if the pod template has multiple containers, each one is a component named ${deployment}/${container}

For each component of the application, the following settings are automatically available when 'adjust --info' is ran:
replicas, mem, cpu (pending: add support for mem\_limit, mem\_request, cpu\_limit, cpu\_request).
If a configuration file is present at ./app.yaml, any custom component settings in it are also returned by 'adjust --info' and map to environment variables of the matching container.

Limitations:
- works only on 'deployment' objects, other types of controllers are not supported.
- minimal tested k8s server version: 1.8.
- if memory or CPU resource limit/request is not set, its value is returned as 0.
- each container in a pod is treated as a separate 'component', however the replicas setting cannot be controlled individually for the containers in the same pod. If 'replicas' is set for multi-container pods and the values are different for the different containers, the last one prevails and will be applied to the pod (and thus to all its containers).

