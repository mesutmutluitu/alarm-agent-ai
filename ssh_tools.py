import subprocess

def execute_ssh_command(ip, username, password, command):
    raise NotImplementedError("SSH bağlantısı bu sürümde kullanılmıyor.")

def execute_local_docker_command(container_name, command):
    full_command = f"docker exec {container_name} bash -c \"{command}\""
    try:
        result = subprocess.check_output(full_command, shell=True, stderr=subprocess.STDOUT, text=True)
        return result
    except subprocess.CalledProcessError as e:
        return f"[ERROR] Komut çalıştırılamadı: {e.output}"