#!/usr/bin/env python3
"""
Debug RAGAnything initialization to find where lightrag becomes None
"""
import asyncio
import os
import sys

# Add paths
sys.path.insert(0, "E:/RAG-Anything")
sys.path.insert(0, "E:/RAG-Anything/backend")

from raganything import RAGAnything, RAGAnythingConfig
from lightrag.utils import EmbeddingFunc

async def debug_init():
    """Debug RAGAnything initialization step by step"""

    working_dir = "E:/RAG-Anything/data/debug_kb"
    os.makedirs(working_dir, exist_ok=True)

    print("=" * 80)
    print("Debugging RAGAnything Initialization")
    print("=" * 80)

    # Step 1: Create config
    print("\n[Step 1] Creating RAGAnythingConfig...")
    config = RAGAnythingConfig(
        working_dir=working_dir,
        parser="mineru",
        parse_method="auto",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )
    print(f"  Config created successfully")

    # Step 2: Create embedding function
    print("\n[Step 2] Creating embedding function...")
    async def embedding_func(texts):
        import openai
        client = openai.AsyncOpenAI(
            api_key="sk-test",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        response = await client.embeddings.create(
            model="text-embedding-v3",
            input=texts,
            encoding_format="float"
        )
        return [item.embedding for item in response.data]
    print("  Embedding function created")

    # Step 3: Create LLM function
    print("\n[Step 3] Creating LLM function...")
    async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        import openai
        client = openai.AsyncOpenAI(
            api_key="sk-test",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    print("  LLM function created")

    # Step 4: Create RAGAnything instance
    print("\n[Step 4] Creating RAGAnything instance...")
    rag = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=8192,
            func=embedding_func
        ),
    )
    print(f"  RAGAnything instance created")
    print(f"  rag.lightrag = {rag.lightrag}")
    print(f"  rag._parser_installation_checked = {rag._parser_installation_checked}")

    # Step 5: Set installation check flag
    print("\n[Step 5] Setting _parser_installation_checked = True...")
    rag._parser_installation_checked = True
    print(f"  Flag set: rag._parser_installation_checked = {rag._parser_installation_checked}")

    # Step 6: Initialize LightRAG
    print("\n[Step 6] Calling _ensure_lightrag_initialized()...")
    init_result = await rag._ensure_lightrag_initialized()
    print(f"  Initialization result: {init_result}")
    print(f"  rag.lightrag = {rag.lightrag}")
    print(f"  rag.lightrag type: {type(rag.lightrag)}")

    if init_result.get("success"):
        print("\n[SUCCESS] RAGAnything initialized successfully!")
        print(f"  LightRAG type: {type(rag.lightrag)}")
        print(f"  Has ainsert method: {hasattr(rag.lightrag, 'ainsert')}")
        return True
    else:
        print(f"\n[ERROR] Initialization failed:")
        print(f"  Error: {init_result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_init())
    sys.exit(0 if success else 1)
