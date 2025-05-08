import re
import json

import openai

from loguru import logger

client = openai.Client(base_url="http://127.0.0.1:30000/v1", api_key="None")

base_context = """
Ты помощник поиска в маркетплейсе.
Тебе необходимо определить, соответствует ли товар и его характеристики поисковому запросу.

Классы запросов:
relevant - товары, которые можно купить по указанному запросу
irrelevant - товары, которые было бы странно увидеть по указанному запросу

Товар:
{item}

Запрос:
{query}

Определи релевантность запроса товару. Отвечай только "relevant" или "irrelevant". Не пиши объяснений и ничего больше.
"""

def read_queries():
    with open('responses.json', 'r') as f:
        data = json.load(f)

    text = data['query_1']
    lines = text.split('\n')
    result = []
    for line in lines:
        line = re.sub(r'[^ЁёА-яA-z ]', '', line).lstrip()
        if line:
            result.append(line)
    return result


def analyse_query(query):
    with open(f'search_responses/{query}.json', 'r') as f:
        response = json.load(f)

    goods = response['results']['sources']

    relevant = []
    irrelevant = []
    for item in goods:
        request = {
            "role": "user",
            "content": base_context.format(item=item, query=query)
        }
    
        response = client.chat.completions.create(
            model="qwen32b",
            messages=[
                {"role": "system", 
                 "content": "You are a helpful AI assistant"},
                request
            ],
            temperature=0,
            max_tokens=3,
        )
        prediction = response.choices[0].message.content.strip().lower()
        
        output = {
            'item_id': item['id'],
            'title': item['title'],
            'score': item['score'],
        }
        if prediction == 'relevant':
            relevant.append(output)
        elif prediction == 'irrelevant':
            irrelevant.append(output)
        else:
            logger.error(prediction)
    
    logger.info(f"Запрос: {query}")
    logger.info(f"Релевантные документы: {len(relevant)}")
    logger.info(f"Нерелевантные документы: {len(irrelevant)}")
    logger.info(f"==========")
    logger.info(f"Релевантные документы: {relevant}")
    logger.info(f"Нерелевантные документы: {irrelevant}")
    logger.info(f"==========")
    r = {
        'Релевантные документы': relevant,
        'Нерелевантные документы': irrelevant
    }
    
    with open(f'./relevanse_results/{query}.json', 'w') as f:
        json.dump(r, f)


if __name__ == '__main__':
    queries = read_queries()

    for query in queries:
        analyse_query(query)
    
    
