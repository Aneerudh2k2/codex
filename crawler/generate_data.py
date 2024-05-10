# %%
from multiprocessing.pool import ThreadPool
import os
import traceback
import click
from crawler.types import (
    PaperAnalysisPrompt,
    PaperAnalysisResponse,
    PaperAnalysisRun,
    ProcessedPaper,
    process_response,
)
from loguru import logger
import httpx
import dotenv
from crawler.serializers import NdjsonReader
from pathlib import Path
import random
from tqdm import tqdm
import requests
import json
import time

dotenv.load_dotenv("../.env.dev")

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def get_completion(prompt):
    res = httpx.post(
        "https://api.mistral.ai/v1/chat/completions",
        json={
            "model": "mistral-large-latest",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.1,
            "top_p": 1,
            "max_tokens": 8192,
            "stream": False,
            "safe_prompt": False,
            "random_seed": 1337,
        },
        headers={
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=120,
    )
    
    
    
    if res.status_code != 200:
        logger.error(f"Failed to get completion: {res.text}")
        return None

    time.sleep(60/60)
    
    print(dict(res.json()))

    json = res.json()

    return json["choices"][0]["message"]["content"]


def get_completion_groq(prompt):
    res = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
            "model": "llama3-70b-8192",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.1,
            "top_p": 1,
            "max_tokens": 8192,
            "stream": False,
        },
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=120,
    )
    
    if res.status_code != 200:
        logger.error(f"Failed to get completion: {res.text}")
        return None
    
    # 30 requests per minute
    time.sleep(60/30)
    
    print(dict(res.json()))

    json = res.json()

    return json["choices"][0]["message"]["content"]

def get_completion_gemini(user_input):
    import requests
    import json 
    import os
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={GOOGLE_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": user_input
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 1,
            "topK": 0,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "stopSequences": []
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    # 60 requests per minute
    time.sleep(60/60)
    
    print(dict(response.json()))
    
    return dict(response.json())["candidates"][0]["content"][0]["parts"][0]["text"]


def get_completion_vertexai(prompt):

    url = "https://us-central1-aiplatform.googleapis.com/v1/projects/chatbot-405211/locations/us-central1/publishers/google/models/gemini-1.0-pro-002:generateContent"

    payload = json.dumps({
    "contents": [
        {
        "role": "user",
        "parts": [
            {
            "text": prompt
            }
        ]
        }
    ],
    "safety_settings": {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_LOW_AND_ABOVE"
    },
    "generationConfig": {
        "temperature": 1,
        "topP": 0.8,
        "topK": 40,
        "maxOutputTokens": 8192,
        "candidateCount": 1,
        "responseMimeType": "text/plain"
    }
    })

    access_token = "ya29.c.c0AY_VpZiBxgwGuC0S_22dI3_cwyu5e7_rofYkv95wBg1xsbWZPFhkIMcoiaFe2P9hFGgrchNKrMzdX32mH8kzPCW677vz55SXVnwd-kaWOGGTgQQspGLzvs0XSeX40D7QGG2B8WUFuMjnh5t_6uX98bdZDtu03usrlKaoDxV0icoMIFvkFOwFjIvVs-BHnnOWQf55MuCf4PsK-1qrKB-JP332GktvzWy6d2lrMmfE6xzWN1E1VeQ595iw5XyTnOSqFDZ1xNXfoG8Yw0-UMyYHTKAeOXJhkmcMjQO_ub9EMh2W0Vy3U7W7HeDdZewvZ5LGndmpI0pcajBMXF87X49E0p2CMBR0jg8yLUKUn3_-Iqh20a2jIH_nRdlYeKCx_pGo0Pu0zA0X9oQRuQEnspOT2ygtiA8mJvKJst-5C6TLp-wdZfUZVE82tH51rAss0WgE456CkvwSz1pftSnbrtwofh8d72iBXZh9xWZUoF3qqFh16J99hfY3qWRgY_iBZgetxxhx3Qh1bfgddwV5iUmOp484O9RVZUBbr-h5tpn56pa5B5pknqMWjxax_-hIjfXQrR14ip1gJ9w1MpcvFQhcIaXvFp9WJ04Y3cyhQovzXU4zFdrjh-oVpFtBFkgIcvv-gs23p68V67BhxjyOX-9qSZe01g6jZp7su73tn7m0nFpWQ17wIMOFhwoIl7o9mxI4w1x0JWeptdYB6ewxbx7ho-hh2Sjjja0p2Xtc1pdd1cffFxQf2sdh6VyIdBOxWnRmgnepldI0vxvIm3UrMvxtBmBci31BR3MOzfZI16pVJ9yF0bzUR5yzkebR0QfW_ac0S8OgpeqSfV647lXdugohe9bv-7onqq7jUUdxq4kBQ5bwZFuiQB5206YYb5bMIM6OpufZW9MjZd7aQiIV2Xu5Y20qwlWhr7mzO2nJuVBFqYRJhB0Q3ciiy_2wmbbixdSrgs5oVBgx78baXYc3UmZnsaeOo0m9h0rBdejjhg4mn94SYkO3U6IRcao"

    headers = {
    'Authorization': f'Bearer {access_token}',  # Replace with your actual API key
    'Content-Type': 'application/json'
    }


    response = requests.request("POST", url, headers=headers, data=payload)

    print(dict(response.json()))
    response.raise_for_status()  # Raise an exception for non-2xx status codes


    return dict(response.json())["candidates"][0]["content"]["parts"][0]["text"]
  


@click.group()
def cli():
    pass


@cli.command()
def prepare():
    sample_rate = 0.02

    prompts: list[PaperAnalysisPrompt] = []

    with NdjsonReader(
        Path("data/processed/cs_inlined_papers.jsonl"), ProcessedPaper, validate=True
    ) as f:
        for p in tqdm(f):
            if random.random() < sample_rate:
                prompt = PaperAnalysisPrompt(paper=p)
                prompts.append(prompt)

    with open("data/raw/finetune_prompts.jsonl", "w") as f:
        for prompt in prompts:
            f.write(prompt.model_dump_json())
            f.write("\n")


def run_prompt(prompt: PaperAnalysisPrompt):
    prompt_str = prompt.compile_prompt()
    try:
        # completion = get_completion(prompt_str)
        
        # time.sleep(60/30)
        # completion = get_completion_groq(prompt_str)
        
        # time.sleep(60/60)
        # completion = get_completion_gemini(prompt_str)
        
        time.sleep(60/60)
        completion = get_completion_vertexai(prompt_str)

        
        response = PaperAnalysisResponse.from_response(completion)
        process_response(response)
    except Exception:
        print(traceback.format_exc())
        return None

    return PaperAnalysisRun(prompt=prompt, response=response)


@cli.command()
def execute():
    prompts: list[PaperAnalysisPrompt] = []
    with NdjsonReader(
        Path("data/raw/finetune_prompts.jsonl"), PaperAnalysisPrompt, validate=True
    ) as f:
        for prompt in f:
            prompts.append(prompt)

    num_failed = 0

    with open("data/raw/finetune_responses.jsonl", "w") as f:
        with ThreadPool(64) as pool:
            for response in tqdm(pool.imap_unordered(run_prompt, prompts)):
                if response is None:
                    num_failed += 1
                    logger.warning("Error processing prompt")
                    continue
                f.write(response.model_dump_json())
                f.write("\n")

    logger.info(f"Failed to process {num_failed} prompts")


if __name__ == "__main__":
    get_completion_vertexai("Hi how are you?")
    cli()
