# test_openai_key.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'API key works!'"}],
        max_tokens=10
    )
    print("✅ Token funciona correctamente!")
    print(f"Respuesta del modelo: {response.choices[0].message.content}")
    print(f"Modelo usado: {response.model}")
except Exception as e:
    print(f"❌ Error al conectar con OpenAI: {e}")