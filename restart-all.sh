#!/bin/bash
systemctl --user restart synthia-backend
systemctl --user restart synthia-frontend-dev
#systemctl --user restart synthia-frontend-build
echo "🔁 All Synthia services restarted successfully."
