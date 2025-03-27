from fastapi import FastAPI
from pydantic import BaseModel
from local_llm import OllamaLLM
from ssh_tools import execute_ssh_command
from logger import log_event
import time

app = FastAPI()
llm = OllamaLLM(model="mistral", endpoint_url="http://localhost:2030")

class AlarmRequest(BaseModel):
    ip: str
    alarm: str

def prompt_next_command(history, attempt=1):
    prompt = f"""
Sen bir Linux sistem analiz aracısın. Aşağıda alarm mesajı ve geçmiş çıktılar yer alıyor.
{f"{attempt}. deneme başarısız oldu." if attempt > 1 else ""}
Her adımda bir önceki çıktıya göre yeni bir komut öner ve neden önerdiğini belirt.

Geçmiş:
{history}

Yeni komut önerilecekse format:
KOMUT: <komut>
AÇIKLAMA: <neden bu komut?>

Eğer analiz aşamasına geçilecekse şu formatta devam et:
ANALİZ:
Lütfen şimdiye kadar topladığın bilgilerle 5 Why (5 Neden) tekniğine göre bu alarmı analiz et:

1. Alarm neden oluştu?
2. Bu durumun arkasındaki neden nedir?
3. Bir önceki sebebin kökeni nedir?
4. Bu durumun oluşmasına sebep olan sistemsel/operasyonel neden ne olabilir?
5. En derin neden nedir?

Her aşamayı teknik ve kısa cümlelerle açıkla.
"""
    return llm(prompt)

def prompt_final_conclusion(history):
    prompt = f"""
Aşağıda bir sistem alarmı için yapılmış 5 WHY analizi yer alıyor:

{history}

Bu analize göre en makul kök nedeni (root cause) kısa ve öz şekilde yaz:
KÖK SEBEP: <tek cümlelik nihai neden>
"""
    return llm(prompt)

def check_command_exists(ip, command):
    base_cmd = command.split()[0]
    check_cmd = f"command -v {base_cmd} >/dev/null 2>&1 && echo 'OK' || echo 'NOT_FOUND'"
    result = execute_ssh_command(ip, check_cmd)
    return "OK" in result

@app.post("/analyze")
async def analyze_alarm(payload: AlarmRequest):
    ip = payload.ip
    alarm = payload.alarm

    history = f"ALARM: {alarm}"
    log_event(ip, alarm, "START", "Analiz başladı.")

    while True:
        for attempt in range(1, 6):
            response = prompt_next_command(history, attempt).strip()

            if response.startswith("ANALİZ:"):
                analysis = response.replace("ANALİZ:", "").strip()
                log_event(ip, alarm, "5WHY", analysis)

                conclusion = prompt_final_conclusion(analysis).strip()
                log_event(ip, alarm, "ROOT_CAUSE", conclusion)

                return {
                    "status": "ok",
                    "5why_analysis": analysis,
                    "root_cause": conclusion.replace("KÖK SEBEP:", "").strip()
                }

            if "KOMUT:" in response:
                lines = response.split("\n")
                command = next((line.replace("KOMUT:", "").strip() for line in lines if line.startswith("KOMUT:")), "")
                explanation = next((line.replace("AÇIKLAMA:", "").strip() for line in lines if line.startswith("AÇIKLAMA:")), "")

                log_event(ip, alarm, "COMMAND_PROPOSED", f"{command}\nAçıklama: {explanation}")

                if check_command_exists(ip, command):
                    output = execute_ssh_command(ip, command)
                    history += f"\n\n> {command}\n{output.strip()}"
                    log_event(ip, alarm, "COMMAND_EXECUTED", f"{command}\nÇıktı:\n{output.strip()}")
                    break
                else:
                    history += f"\n\n> {command}\n[Komut bulunamadı]"
                    log_event(ip, alarm, "COMMAND_MISSING", command)
                    time.sleep(1)
            else:
                log_event(ip, alarm, "ERROR", f"Beklenmeyen format:\n{response}")
                return {"status": "error", "message": "Beklenmeyen yanıt formatı", "raw_response": response}

        else:
            log_event(ip, alarm, "FAILURE", "5 denemede de geçerli komut önerilemedi.")
            return {"status": "fail", "message": "5 farklı komut önerisi başarısız oldu."}