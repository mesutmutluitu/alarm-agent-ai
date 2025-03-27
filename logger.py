from datetime import datetime

def log_event(ip, alarm, step, content):
    log_line = f"[{datetime.now().isoformat()}] [{ip}] [{alarm}] [{step}]\n{content}\n{'-'*60}\n"
    with open("analysis_log.txt", "a") as f:
        f.write(log_line)