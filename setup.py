from setuptools import find_packages, setup


setup(
    name="pm-proj-rag",
    version="0.1.0",
    description="Facts-only mutual fund FAQ assistant using a fixed Groww corpus.",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    install_requires=[
        "fastembed>=0.3.0",  # BGE embeddings
        "faiss-cpu>=1.7.4",  # Vector similarity search
        "groq>=0.8.0",  # LLM API (Llama 3.1)
        "fastapi>=0.104.0",  # API framework
        "uvicorn>=0.24.0",  # ASGI server
        "pydantic>=2.0",  # Data validation
        "python-dotenv>=1.0",  # Environment variables
        "requests>=2.31.0",  # HTTP requests
        "beautifulsoup4>=4.12.0",  # HTML parsing
        "pyyaml>=6.0",  # Config files
        "sentence-transformers>=2.2.0",  # Cross-encoder reranking
    ],
)

