from ssh_tools import execute_ssh_command

def run_all_commands(ip, command_list):
    results = []
    for cmd in command_list:
        output = execute_ssh_command(ip, cmd)
        results.append((cmd, output))
    return results