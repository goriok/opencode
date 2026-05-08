# kftray Configurations

This directory contains kftray JSON configuration files for port-forward management.

## Purpose

kftray uses JSON files to define port-forward configurations that can be imported into the GUI/TUI. These configs define which Kubernetes services to expose locally.

## Files

- `litellm-remote.json` - Port-forward config for LiteLLM service running in the remote cluster

## Usage

### Import via kftray GUI
1. Open kftray app
2. Go to Settings → Import
3. Select the JSON file from this directory

### Import via kftui (TUI)
```bash
kftui import litellm-remote.json
```

## Config Format

Each JSON file contains an array of configuration objects with the following fields:

- `alias`: Human-readable name for the port-forward
- `context`: Kubernetes context to use
- `kubeconfig`: Path to kubeconfig file (empty for default)
- `local_port`: Local port to bind to
- `namespace`: Kubernetes namespace of the service
- `protocol`: Protocol to use (tcp/udp)
- `remote_port`: Target port on the service
- `service`: Kubernetes service name
- `workload_type`: Type of workload (service/deployment/statefulset)

## References

- kftray documentation: https://kftray.app/docs
- kftray config format: https://kftray.app/blog/kftray-manage-all-k8s-port-forward#managing-configurations-locally-json-format
