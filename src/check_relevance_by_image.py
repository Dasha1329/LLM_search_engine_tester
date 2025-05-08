import re
import time
import json
import argparse

import openai

from loguru import logger
from elasticsearch6 import Elasticsearch

class RelevanceModel():

    def __init__(self):
        self.client = openai.Client(base_url="http://127.0.0.1:30000/v1", api_key="None")


    def process_query(self, query, product_name, product_photo_link):
        system = f"""\
Ты ведущий эксперт команды поиска в маркетплейсе. Твоя задача — определить, соответствует ли товар и его изображение запросу из поисковой выдачи. При этом анализируй как текстовое описание товара, так и фото.

Варианты ответов:
	•	relevant — товар, который подходит под указанный запрос, а его фото соответствует описанию и намерению запроса.
	•	irrelevant — товар, который не соответствует запросу или чье изображение вводит в заблуждение.

Step-by-step reasoning:
1. Проверяем, относится ли товар к категории, запрашиваемой пользователем.
2. Проверяем, есть ли в описании товара характеристики, соответствующие запросу.
3. Проверяем изображение: оно должно точно отражать товар, который подходит запросу, включая его внешний вид, форму, цвет, и другие ключевые визуальные характеристики.
4. Делаем вывод о релевантности.

Пример 1:
Запрос: "телефон с хорошей камерой"
Товар: "Смартфон Xiaomi 13 Pro, камера 200 МП, 256 ГБ памяти"
Step-by-step reasoning:
1. Выделяем главное слово в запросе (телефон) и товаре (Cмартфон). 
2. Проверяем, совпадают ли по смыслу главные слова в запросе и товаре: да, телефон и Смартфон это одно и тоже
2. Проверяем, упоминается ли камера в характеристиках. Ответ: Да, 200 МП.
3. Сравниваем характеристики камеры с запросом "хорошая камера". Ответ: Да, камера высокого качества.
Вывод: relevant

Пример 2:
Запрос: "чехол на iphone 15"
Товар: "Iphone 15, камера 200 МП"
Step-by-step reasoning:
1. Выделяем главное слово в запросе (чехол) и товаре (Iphone). 
2. Проверяем, совпадают ли по смыслу главные слова в запросе и товаре: нет
Вывод: irrelevant
"""
        
        system_query = f"""\
Оцени соответствие товара и его изображения запросу.
Товар: {product_name}
Запрос: {query}
"""
        
        messages = [
            {"role": "user", "content": [{"type": "text", "text": system}]}
        ]
    
        # ссылка на изображение
        if product_photo_link:
            messages[0]["content"].append(
                {"type": "image_url", "image_url": {"url": product_photo_link}}
            )
    
        messages[0]["content"].append({"type": "text", "text": system_query})
    
        try:
            response = self.client.chat.completions.create(
                model="Qwen2-VL-72B-Instruct-AWQ",
                messages=messages,
            )
    
            prediction = response.choices[0].message.content.strip().lower()
            # выделяем одно слово relevamt/irrelevant из длинного рассуждения ллм
            if "irrelevant" in prediction:
                prediction = "irrelevant"
                return prediction
            elif "relevant" in prediction:
                prediction = "relevant"
                return prediction
            else:
                raise ValueError(f"Unexpected response format: {prediction}")
        except Exception as e:
            print(f"Error processing item {query} {product_name}: {e}")


llm = RelevanceModel()


def get_item_by_id(items):
    es = Elasticsearch(hosts='http://elastic-lb-01.prod.lan:19200/')
    data_query = {
        "query": {
            "ids": {
                "values": items
            }
        }
    }
    response = es.search(index='item_index_v7', body=data_query)
    if response['hits']['total'] < 1:
        raise Exception("Item not found")
    return response['hits']['hits']


def analyse_query(query_data):
    query = query_data['query']
    logger.info(f"Process {query}")

    
    items = query_data['search_response']['results']['items']

    logger.info(f"Get data from ES")
    response = get_item_by_id(items)
    mapping = {response[i]['_id']:i for i in range(len(items))}
    items_info = {response[i]['_id']:response[i] for i in range(len(items))}
    
    results = []
    for item in items:
        info = response[mapping[item]]

        product_name = info['_source']['long_web_name']
        product_photo_link = 'https://main-cdn.sbermegamarket.ru/big2' + info['_source']['images'][0]['image_link']
        product_attributes = [{item["name"]: item["value"]} for item in item_data['_source']['attributes']]
        
        logger.info(f"Question in LLM")
        answer = llm.process_query(query, product_name, product_photo_link, product_attributes)
        results.append({'item_id': item, 'answer': answer})
        

    return results, items_info

def read_queries(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    return data

def main(args):
    data = read_queries(args.output_path)
    print(len(data))
    for key in data:
        item = data[key]
        try:
            result, items_info = analyse_query(item)
        except Exception as e:
            continue
        data[key]['result'] = result
        data[key]['items_info'] = items_info

    with open(args.output_path, 'w') as f:
        json.dump(data, f)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str)
    args = parser.parse_args()

    main(args)
    
    
