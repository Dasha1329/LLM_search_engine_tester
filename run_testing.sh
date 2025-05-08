#!/bin/bash

OUTPUT_PATH="./data/rare_queries.json"


# python src/generate_query.py --output_path $OUTPUT_PATH --num_responses 2 
python src/get_serps.py --output_path $OUTPUT_PATH
python src/check_relevance_by_image.py --output_path $OUTPUT_PATH