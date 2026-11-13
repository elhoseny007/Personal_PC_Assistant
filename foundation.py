import numpy as np
import pandas as pd
#concurancy
import asyncio
#arguments
import json
#using with cach
import redis
#time
import time 
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
#client
from groq import Groq 
#rag
#extract document
from llama_index.core import SimpleDirectoryReader,Settings
#splitting
from llama_index.core.node_parser import SemanticSplitterNodeParser
#embedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
#retrieval
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import VectorIndexRetriever,QueryFusionRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.evaluation import FaithfulnessEvaluator,RelevancyEvaluator,CorrectnessEvaluator
#vector database
import faiss
from tavily import TavilyClient

#api
GROQ_API_KEY=os.getenv('GROQ_API_KEY')
TAVILY_API_KEY=os.getenv('TAVILY_API_KEY')
#model
SIMPLE_MODEL=os.getenv('SIMPLE_MODEL')
COMPLEX_MODEL=os.getenv('COMPLEX_MODEL')
embedding_model=os.getenv("EMBEDDING_MODEL")
#client
client = Groq(api_key=GROQ_API_KEY, timeout=10)
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")
Tavily_Client=TavilyClient(api_key=TAVILY_API_KEY)
if not Tavily_Client:
    raise ValueError("TAVILY_API_KEY is missing from .env")
print("API KEY LOADED:", bool(GROQ_API_KEY))
print("API KEY LENGTH:", len(GROQ_API_KEY))