from fastapi import FastAPI
from pydantic import BaseModel
from local_llm import OllamaLLM
from ssh_tools import execute_local_docker_command
from logger import log_event
import time

app = FastAPI()
llm = OllamaLLM(model="mistral", endpoint_url="http://localhost:11434/api/generate")

CONTAINER_ID = "0b0a7d92a557"

class AlarmRequest(BaseModel):
    alarm: str

def build_prompt_for_command(history: str, attempt: int = 1) -> str:
    return f"""
Sen bir Linux sistem analiz aracısın. Aşağıda alarm mesajı ve geçmiş çıktılar yer alıyor.
{f"{attempt}. deneme başarısız oldu." if attempt > 1 else ""}
Her adımda bir önceki çıktıya göre yeni bir komut öner ve neden önerdiğini belirt.

Geçmiş:
{history}

Yeni komut önerilecekse format:
KOMUT: <komut>
AÇIKLAMA: <neden bu komut?>
"""

def build_prompt_for_analysis(history: str) -> str:
    return f"""
Lütfen aşağıdaki bilgilerle 5 Why (5 Neden) analizini yap:

{history}

1. Alarm neden oluştu?
2. Bu durumun arkasındaki neden nedir?
3. Bir önceki sebebin kökeni nedir?
4. Bu durumun oluşmasına sebep olan sistemsel/operasyonel neden ne olabilir?
5. En derin neden nedir?
"""

def build_prompt_for_conclusion(analysis: str) -> str:
    return f"""
Aşağıdaki 5 WHY analizine dayanarak nihai kök nedeni tek cümleyle özetle:

{analysis}

KÖK SEBEP: <tek cümlelik neden>
"""

def request_command_from_llm(history: str, attempt: int = 1) -> str:
    prompt = build_prompt_for_command(history, attempt)
    print(f"\n🧠 AI'ya şu prompt ile komut önerisi soruluyor:\n{prompt}\n")
    return llm.invoke(prompt)

def request_analysis_from_llm(history: str) -> str:
    prompt = build_prompt_for_analysis(history)
    print(f"\n🧠 AI'dan şu verilerle 5WHY analizi isteniyor:\n{prompt}\n")
    return llm.invoke(prompt)

def request_conclusion_from_llm(analysis: str) -> str:
    prompt = build_prompt_for_conclusion(analysis)
    print(f"\n🧠 AI'dan şu analizle kök neden isteniyor:\n{prompt}\n")
    return llm.invoke(prompt)

def check_command_exists(command):
    if not command or not command.strip():
        return False
    parts = command.strip().split()
    if not parts:
        return False
    base_cmd = parts[0]
    check_cmd = f"command -v {base_cmd} >/dev/null 2>&1 && echo 'OK' || echo 'NOT_FOUND'"
    result = execute_local_docker_command(CONTAINER_ID, check_cmd)
    return "OK" in result

@app.post("/analyze")
async def analyze_alarm(payload: AlarmRequest):
    alarm = payload.alarm
    container = CONTAINER_ID

    print(f"\n🚨 Alarm alındı: [{container}] -> {alarm}\n")
    history = f"ALARM: {alarm}"
    log_event(container, alarm, "START", "Analiz başladı.")

    while True:
        for attempt in range(1, 6):
            response = request_command_from_llm(history, attempt).strip()

            if response.startswith("ANALİZ:"):
                analysis = response.replace("ANALİZ:", "").strip()
                log_event(container, alarm, "5WHY", analysis)
                print("\n✅ 5WHY analizi tamamlandı.\n")
                print(f"🔎 ANALİZ SONUCU:\n{analysis}\n")

                conclusion = request_conclusion_from_llm(analysis).strip()
                log_event(container, alarm, "ROOT_CAUSE", conclusion)
                print(f"🔍 KÖK NEDEN BULUNDU:\n{conclusion}\n")

                return {
                    "status": "ok",
                    "5why_analysis": analysis,
                    "root_cause": conclusion.replace("KÖK SEBEP:", "").strip()
                }

            if "KOMUT:" in response:
                lines = response.split("\n")
                command = next((line.replace("KOMUT:", "").strip() for line in lines if line.startswith("KOMUT:")), "")
                explanation = next((line.replace("AÇIKLAMA:", "").strip() for line in lines if line.startswith("AÇIKLAMA:")), "")

                log_event(container, alarm, "COMMAND_PROPOSED", f"{command}\nAçıklama: {explanation}")
                print(f"🛠️ AI ÖNERİSİ:\nKomut: {command}\nAçıklama: {explanation}\n")

                if check_command_exists(command):
                    output = execute_local_docker_command(container, command)
                    history += f"\n\n> {command}\n{output.strip()}"
                    log_entry = f"{command}\nÇıktı:\n{output.strip()}"
                    log_event(container, alarm, "COMMAND_EXECUTED", log_entry)
                    print(f"✅ Komut çalıştırıldı: {command}")
                    print(f"📤 Komut Çıktısı:\n{output.strip()}\n")
                    print(f"🧾 GÜNCEL HISTORY:\n{history}\n")
                    break
                else:
                    history += f"\n\n> {command}\n[Komut bulunamadı]"
                    log_event(container, alarm, "COMMAND_MISSING", command)
                    print(f"⚠️ Komut sistemde yok: {command}\n")
                    time.sleep(1)
            else:
                log_event(container, alarm, "ERROR", f"Beklenmeyen format:\n{response}")
                print("❌ Beklenmeyen yanıt formatı alındı.\n")
                return {"status": "error", "message": "Beklenmeyen yanıt formatı", "raw_response": response}

        else:
            log_event(container, alarm, "FAILURE", "5 denemede de geçerli komut önerilemedi.")
            print("❌ 5 farklı komut önerisi başarısız oldu.\n")
            return {"status": "fail", "message": "5 farklı komut önerisi başarısız oldu."}
