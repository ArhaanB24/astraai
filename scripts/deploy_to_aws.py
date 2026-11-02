import subprocess, json, tempfile, os, time, sys, tarfile

aws_cmd = r'C:\Users\ajay\AppData\Roaming\Python\Python313\Scripts\aws.cmd'
instance_id = 'i-0add35ffc751ec0a5'
s3_bucket = 'arthaai-user-storage-195231312586'
base_dir = r'c:\Users\ajay\Downloads\ArthaAI\ArthaAI'

EXCLUDE_DIRS = {
    '.git', '.next', 'node_modules', '__pycache__', '.pytest_cache', 
    'venv', '.venv', '.gemini', 'dist', 'build', '.idea', '.vscode'
}

def make_tar(output_filename, source_dir):
    print("1. Packaging updated project into", output_filename, "...")
    with tarfile.open(output_filename, "w:gz") as tar:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.endswith('.egg-info')]
            for file in files:
                if file.endswith(('.pyc', '.log', '.tar.gz', '.pem', '.swp')):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                tar.add(full_path, arcname=rel_path)
    print("Tarball created. Size:", os.path.getsize(output_filename), "bytes")

def run_remote_command(commands):
    params = {'commands': commands}
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as f:
        json.dump(params, f)
        f_name = f.name
    
    cmd = [
        aws_cmd, 'ssm', 'send-command',
        '--instance-ids', instance_id,
        '--document-name', 'AWS-RunShellScript',
        '--parameters', f'file://{f_name}',
        '--region', 'ap-south-1'
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(f_name)
    if res.returncode != 0:
        print('Error sending SSM command:', res.stderr)
        return None
    out = json.loads(res.stdout)
    cmd_id = out['Command']['CommandId']
    print("SSM Command Sent (ID: " + cmd_id + "). Waiting for execution on EC2...")
    
    for _ in range(120):
        time.sleep(3)
        cmd2 = [
            aws_cmd, 'ssm', 'get-command-invocation',
            '--command-id', cmd_id,
            '--instance-id', instance_id,
            '--region', 'ap-south-1'
        ]
        res2 = subprocess.run(cmd2, capture_output=True, text=True)
        if res2.returncode == 0:
            out2 = json.loads(res2.stdout)
            status = out2.get('Status')
            if status in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
                return out2
            print(".", end="", flush=True)
    return None

if __name__ == '__main__':
    tar_path = os.path.join(base_dir, "arthaai_deploy.tar.gz")
    make_tar(tar_path, base_dir)

    print("2. Uploading deployment package to AWS S3...")
    s3_key = "deploy/arthaai_deploy.tar.gz"
    s3_uri = f"s3://{s3_bucket}/{s3_key}"
    res_s3 = subprocess.run([aws_cmd, "s3", "cp", tar_path, s3_uri], capture_output=True, text=True)
    print(res_s3.stdout)

    print("3. Generating S3 presigned URL for secure curl download on EC2...")
    res_presign = subprocess.run([
        aws_cmd, "s3", "presign", s3_uri, "--expires-in", "3600", "--region", "ap-south-1"
    ], capture_output=True, text=True)
    presigned_url = res_presign.stdout.strip()
    print("Presigned URL generated.")

    print("4. Executing remote clean build & redeployment on EC2...")
    remote_commands = [
        f'curl -fsSL "{presigned_url}" -o /tmp/arthaai_deploy.tar.gz',
        "mkdir -p /home/ubuntu/ArthaAI",
        "tar -xzf /tmp/arthaai_deploy.tar.gz -C /home/ubuntu/ArthaAI",
        "chown -R ubuntu:ubuntu /home/ubuntu/ArthaAI",
        "cd /home/ubuntu/ArthaAI && docker compose build frontend backend",
        "cd /home/ubuntu/ArthaAI && docker compose down",
        "cd /home/ubuntu/ArthaAI && docker compose up -d",
        "sleep 5",
        "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
    ]
    
    exec_res = run_remote_command(remote_commands)
    if exec_res:
        print("\nDeployment Execution Status:", exec_res.get('Status'))
        print("Standard Output:\n", exec_res.get('StandardOutputContent'))
        if exec_res.get('StandardErrorContent'):
            print("Standard Error:\n", exec_res.get('StandardErrorContent'))
