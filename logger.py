from datetime import datetime

def log_event(target, alarm, step, content):
    log_line = f"[{datetime.now().isoformat()}] [{target}] [{alarm}] [{step}]\n{content}\n{'-'*60}\n"
    with open("analysis_log.txt", "a") as f:
        f.write(log_line)
