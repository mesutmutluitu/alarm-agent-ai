from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from local_llm import OllamaLLM

llm = OllamaLLM(model="mistral", endpoint_url="http://localhost:2030")

analyzer_prompt = PromptTemplate(
    input_variables=["alarm_text", "command_outputs"],
    template="""
Sunucudan aşağıdaki alarm geldi:
"{alarm_text}"

Aşağıda çalıştırılan komutlar ve çıktıları yer almakta:

{command_outputs}

Tüm çıktılara göre sistemdeki problemi açıkla ve mümkünse çözüm öner.
"""
)

analyzer_chain = LLMChain(llm=llm, prompt=analyzer_prompt)

def analyze_results(alarm_text, command_outputs):
    full_output = ""
    for cmd, out in command_outputs:
        full_output += f"\n### {cmd} ###\n{out}\n"
    return analyzer_chain.run(alarm_text=alarm_text, command_outputs=full_output)