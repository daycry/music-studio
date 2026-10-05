#!/bin/sh
set -eu
python -c 'import torch; print("engine-acestep: attention=SDPA torch=" + torch.__version__, flush=True)'
exec "$@"
