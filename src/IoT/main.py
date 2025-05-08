from pydantic import BaseModel, Field
import os
from llm import OpenAILLM
from string import Template
from iteration_of_thought import GIOT


output_file = "responses.txt"

llm = OpenAILLM(model_name="default")

class QueryAnswer(BaseModel):
    answer: str = Field(description="Final Answer")

PROMPT = Template("""You are a compiler of search queries in the $categories category for the marketplace. 
Your requests are varied (for men, women, children) and similar to human ones.
Make 10 examples of search queries.
                  
Remember the rules:
The length of the request must be exactly 5 words,
The request may include a size indication (e.g. XS, XL, M), but this is not required.

In response, display only queries in Russian.
""")

category="Clothes"

prompt = PROMPT.substitute(categories=category)

def write_responses_to_file(response, output_file):
    if not os.path.exists(output_file):
        print(f"Файл {output_file} не найден. Создаём новый файл.")

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(f"Ответ:\n{response}\n")
    print(f"Все ответы записаны в файл {output_file}.")

def main():
    giot = GIOT(llm=llm, iterations=3, answer_schema=QueryAnswer)
    result = giot.run(prompt)
    write_responses_to_file(result, output_file)

if __name__ == "__main__":
    main()