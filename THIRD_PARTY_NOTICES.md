# Third-Party Notices and Licenses

This project is licensed under the GNU AGPLv3.

To provide its functionality, this project uses the following third-party libraries. Their licensing terms apply in addition to this project’s license. Components with copyleft/commercial terms (e.g., PyQt5 GPL/commercial; PyMuPDF/pymupdf4llm AGPL) are noted; the collective work is released under AGPL-3.0 to satisfy upstream copyleft.

| Package | License (summary) | Notes |
| --- | --- | --- |
| PyQt5 / PyQt5-Qt5 / PyQt5_sip | GPL/commercial | GUI toolkit |
| PyMuPDF | AGPL-3.0 | PDF parsing backend |
| pymupdf4llm | AGPL-3.0 | PDF → markdown helper |
| selenium | Apache-2.0 | Browser automation |
| beautifulsoup4 | MIT | HTML parsing |
| pydantic / pydantic-core | MIT | Settings and validation |
| python-dotenv | BSD-3-Clause | .env loading |
| requests | Apache-2.0 | HTTP client |
| httpx / httpcore | BSD-3-Clause | HTTP client |
| fastapi | MIT | API framework (adapter) |
| starlette | BSD | ASGI toolkit |
| uvicorn | BSD | ASGI server |
| httptools | MIT | HTTP parser |
| uvloop | Apache-2.0 | Event loop |
| watchfiles | MIT | File watcher |
| typer | MIT | CLI helper |
| rich | MIT | Console formatting |
| sqlalchemy | MIT | ORM/query builder |
| psycopg / psycopg-binary | LGPL-3.0 | Postgres driver |
| psycopg2-binary | LGPL-3.0 | Postgres driver |
| pgvector | MIT | pgvector helpers |
| numpy | BSD-3-Clause | Numerics |
| scipy | BSD-3-Clause | Numerics |
| scikit-learn | BSD-3-Clause | ML utilities |
| threadpoolctl | BSD-3-Clause | Threadpool control |
| joblib | BSD-3-Clause | Caching/parallel |
| sentence-transformers | Apache-2.0 | Embedding pipeline |
| transformers | Apache-2.0 | LLM/embedding tooling |
| tokenizers | Apache-2.0 | Tokenization |
| safetensors | Apache-2.0 | Model serialization |
| torch | BSD-style | Backend for embeddings |
| triton | MIT | GPU kernels |
| huggingface-hub | Apache-2.0 | Model hub client |
| hf-xet | Apache-2.0 | HF/Xet helper |
| regex | Apache-2.0 | Regex engine |
| fsspec | BSD | Filesystem spec |
| filelock | Public Domain | File locking |
| packaging | Apache-2.0 | Packaging helpers |
| Markdown | BSD-3-Clause | Markdown processing |
| markdown-it-py / mdurl | MIT | Markdown parsing |
| Pygments | BSD-2-Clause | Syntax highlighting |
| pillow | HPND/PIL | Imaging |
| PyYAML | MIT | YAML parsing |
| Jinja2 / MarkupSafe | BSD-3-Clause | Templating |
| networkx | BSD | Graph utilities |
| sympy | BSD-3-Clause | Symbolic math |
| tabulate | MIT | Tabular formatting |
| PySocks | BSD | Socks support |
| soupsieve | MIT | CSS selectors |
| sortedcontainers | Apache-2.0 | Data structures |
| shellingham | MIT | Shell detection |
| pytest | MIT | Test runner |
| pytest-qt | MIT | Qt test helpers |
| iniconfig | MIT | Config parser |
| pluggy | MIT | Plugin system |
| trio | MIT | Async library |
| trio-websocket | MIT | WebSocket over trio |
| websockets | BSD | WebSocket client/server |
| websocket-client | BSD | WebSocket client |
| wsproto | MIT | WebSocket protocol |
| outcome | MIT | Trio helper |
| fastapi/uvicorn stack deps (h11, httptools) | MIT/BSD | HTTP/ASGI plumbing |
| numpy GPU support (nvidia-*-cu12 wheels) | Various NVIDIA EULAs | CUDA runtime/BLAS/cuDNN/NCCL components |
| tqdm | MPL-2.0 | Progress bars |
| rich | MIT | Console formatting |
| setuptools / wheel | MIT | Packaging tools |

Refer to each project’s repository or wheel metadata for full license texts and obligations. Ensure your usage complies with copyleft components (AGPL/GPL) and NVIDIA EULA terms where applicable.
