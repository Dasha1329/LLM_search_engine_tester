#!/bin/bash

# python -m sglang.launch_server --model-path ../hugging_face_hub/Qwen2.5-32B-Instruct --tp 2 --port 30000 #Генерация запросов

# python -m sglang.launch_server --model-path ../hugging_face_hub/gemma-2-27b-it --port 30000

python -m sglang.launch_server --model-path ../hugging_face_hub/Qwen2-VL-72B-Instruct-AWQ --tp 2 --port 30000 --chat-template qwen2-vl # релевантость запросов