from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from local_llm import OllamaLLM

llm = OllamaLLM(model="mistral", endpoint_url="http://localhost:2030")

planner_prompt = PromptTemplate(
    input_variables=["alarm_text"],
    template="""
PRTG'den aşağıdaki alarm geldi:
"{alarm_text}"

Bu alarmı daha iyi anlamak için hangi Linux komutlarını çalıştırmam gerekir? Komutları sırayla ve sadece komut içeriği olacak şekilde listele:
"""
)

planner_chain = LLMChain(llm=llm, prompt=planner_prompt)

def generate_command_list(alarm_text):
    output = planner_chain.run(alarm_text)
    commands = [line.strip() for line in output.strip().split("\n") if line.strip()]
    return commands