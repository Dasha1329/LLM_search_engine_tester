# Репозиторий по LLM тестировщику

## Установка библиотке

- `conda env create -f environment.yml`

-  `source activate llm-tester`

- `pip install flashinfer -i https://flashinfer.ai/whl/cu121/torch2.4/`

## Запуск

- `python -m sglang.launch_server --model-path PATH_FOR_MODEL/Qwen2.5-32B-Instruct --tp 2 --port 30000`. Запускаем LLM

- `bash run_testing.sh` Запускам процесс тестирования. *Важно!!! Нельзя запускать скрипт очень часто!!! Не чаще 1 раза в 5 минут*

- Привет, я Даша
- 