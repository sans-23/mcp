from backend.models.api_models import Superclass
from openai import OpenAI # type: ignore
from typing import List, Dict, Any, Literal, Optional, Union

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

try:
    model_name = "deepseek/deepseek-r1:free"
    response = client.chat.completions.parse(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Why is the color of sky blue?"
            }
        ],
        response_format=Superclass,
    )
    raw_response_content = response.choices[0].message.content

    print("Raw response content:")
    print(raw_response_content)

except Exception as e:
    print(f"An error occurred: {e}")