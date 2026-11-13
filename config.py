import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq, AuthenticationError

# 1. محاولة تحميل ملف .env صراحة من نفس المجلد
env_path = Path(__file__).parent / ".env"
print(f"Loading .env from: {env_path}")
load_dotenv(env_path, override=True)

# 2. قراءة المفتاح والمتغيرات
groq_key = os.getenv("GROQ_API_KEY")
SIMPLE_MODEL = os.getenv("SIMPLE_MODEL", 'openai/gpt-oss-20b')
COMPLEX_MODEL=os.getenv("COMPLEX_MODEL",'qwen/qwen3.8-27b')
print(f"GROQ_API_KEY found: {'Yes (Length: ' + str(len(groq_key)) + ')' if groq_key else 'NO'}")
if groq_key:
    print(f"Key preview: {groq_key[:6]}...{groq_key[-4:]}")
print(f"SIMPLE_MODEL: {SIMPLE_MODEL}")

# 3. التحقق من الوجود والاتصال
if not groq_key:
    raise ValueError("FAILED: GROQ_API_KEY is missing or empty in .env file!")

try:
    print("\n[*] Initializing Groq client and testing connection...")
    client = Groq(api_key=groq_key, timeout=10)
    
    response = client.chat.completions.create(
        model=SIMPLE_MODEL,
        messages=[{"role": "user", "content": "Say 'OK' if you can read this."}],
        max_tokens=10
    )
    
    print("\n SUCCESS! The API key is valid and the connection is working perfectly.")
    print(f"Response from Groq: {response.choices[0].message.content.strip()}")

except AuthenticationError:
    print("\n AUTHENTICATION ERROR (401): The API key is invalid, revoked, or incorrectly copied.")
except Exception as e:
    print(f"\n ERROR OCCURRED: {type(e).__name__} - {e}")

LANGFUSE_SECRET_KEY=os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY=os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_BASE_URL=os.getenv("LANGFUSE_BASE_URL")