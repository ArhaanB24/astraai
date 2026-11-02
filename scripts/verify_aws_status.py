import sys, os
sys.path.insert(0, os.path.abspath('scripts'))
from deploy_to_aws import run_remote_command

print("Checking remote production status on AWS EC2...")
res = run_remote_command([
    'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"',
    'curl -I http://localhost/',
    'curl -I http://localhost/onboarding',
    'curl -I http://localhost/api/v1/mutual-funds/catalog'
])
if res:
    print("\n--- Command Status:", res.get("Status"))
    print("\n--- Output:\n", res.get("StandardOutputContent"))
    if res.get("StandardErrorContent"):
        print("\n--- Errors:\n", res.get("StandardErrorContent"))
else:
    print("Failed to communicate with EC2.")
