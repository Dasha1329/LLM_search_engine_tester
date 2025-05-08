import os
import json
import random
import asyncio
import argparse

import openai
from openai import AsyncOpenAI
from string import Template


# PROMPT = Template("""Ты-составитель поисковых запросов в категории $categories для маркетплейса. 
# Твои запросы разнообразные (для мужчин, женщин, детей) и похожие на человеческие.
# Составь 10 поисковых запросов.
                  
# Запомни правила:
# - длина запроса должна быть 4-5 слов
# - В запросе может быть указание размера (например, XS, XL, M), но не обязательно

# Примеры запросов:
# Костюм мужской черный XL
# Штаны мужские летние хлопковые
# Детские джинсы летние размер XS

# В ответ выведи только запросы.
# """)

# category="Одежда"

PROMPT = Template("""Ты-составитель поисковых запросов в категории одежда и обувь для маркетплейса. 
Твои запросы разнообразные (для мужчин, женщин, детей) и похожие на человеческие.
Составь 10 поисковых запросов.
                  
Запомни правила:
- Длина запроса должна не более 5 слов
- В запросе может быть указание размера (например, XS, XL, M), но не обязательно
- В запросе обязательно нужно указать сезон (лето, зима осень и т.д.)

Примеры запросов:
Костюм мужской черный XL осень
Штаны мужские летние хлопковые зима
Детские джинсы летние размер XS

В ответ выведи только запросы.
""")

prompt = PROMPT.substitute()

max_retries = 5 
retry_delay = 1  

client = AsyncOpenAI(
        api_key="EMPTY",
        base_url="http://127.0.0.1:30000/v1",
        )

async def fetch_responses_with_retry(prompt, num_responses):
    retries = 0
    while retries < max_retries:
        try:
            response = await client.chat.completions.create(
                model="default",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
                n=num_responses
            )
            return [choice.message.content for choice in response.choices]
        except openai.RateLimitError:
            print(f"Превышен лимит запросов. Повторная попытка через {retry_delay} секунд...")
            await asyncio.sleep(retry_delay * (2 ** retries) + random.uniform(0, 1))
            retries += 1
        except openai.APIError as e:
            print(f"API ошибка: {e}. Повторная попытка через {retry_delay} секунд...")
            await asyncio.sleep(retry_delay * (2 ** retries) + random.uniform(0, 1))
            retries += 1
        except Exception as e:
            print(f"Исключение: {e}. Повторная попытка через {retry_delay} секунд...")
            await asyncio.sleep(retry_delay * (2 ** retries) + random.uniform(0, 1))
            retries += 1

    print("Превышено количество повторных попыток. Пропуск запроса.")
    return ["Ошибка: превышено количество повторных попыток"] * num_responses

def write_responses_to_file(responses, output_path: str):
    final_response = []
    for resp in responses:
        final_response += resp.split('\n')
    
    with open(output_path, "w", encoding="utf-8") as file:
        result = {}
        for i, response in enumerate(final_response):
            result[i] = {"query": response}
        json.dump(result, file)
    print(f"Все ответы записаны в файл {output_path}.")

async def main(args):
    responses = await fetch_responses_with_retry(prompt, args.num_responses)
    write_responses_to_file(responses, args.output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str)
    parser.add_argument('--num_responses', type=int)
    args = parser.parse_args()

    asyncio.run(main(args))