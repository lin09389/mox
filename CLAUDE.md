# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mox is an LLM Adversarial Attack & Defense Platform - a comprehensive Python toolkit for testing and evaluating large language model security.

## Common Commands

```bash
# Run CLI
python -m mox --help

# Run specific attack
python -m mox attack --model gpt-4 --attack-type jailbreak

# Run defense test
python -m mox defend --input "malicious prompt"

# Start API server (FastAPI)
python -m mox api

# Start Web UI (Gradio)
python -m mox ui

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=mox --cov-report=html

# Lint
ruff check mox/
mypy mox/

# Format
black mox/

# Security scan
bandit -r mox/
```

## Architecture

### Core Modules

- **mox/core/llm.py** - Multi-model LLM abstraction layer with `BaseLLM` interface supporting:
  - OpenAI, Anthropic, MiniMax, Google Gemini, DeepSeek, Cohere, Groq, Azure
  - **Local models via Ollama** - Use `OllamaLLM` class with `base_url="http://localhost:11434/v1"`

- **mox/core/llm_gateway.py** - Load balancing across multiple LLM endpoints with failover
- **mox/core/tasks.py** - Async task queue using Celery
- **mox/core/cache.py** - Redis/in-memory caching
- **mox/core/auth.py** - JWT authentication

### Attack Module (mox/attacks/)

Contains 20+ attack implementations:
- `prompt_injection.py` - Direct and advanced prompt injection
- `jailbreak.py` - DAN, Developer Mode, AIM, and other jailbreak templates
- `gcg.py` - Gradient-based token optimization attacks
- `llm_driven.py` - TAP, PAIR, Crescendo, Multi-turn jailbreak
- `agent_attacks.py` - Tool abuse, memory injection, role hijacking
- `rag_attacks.py` - RAG system attacks
- `orchestrator.py` - **NEW** Unified attack orchestration framework

### Defense Module (mox/defense/)

- `input_filter.py` - Keyword detection, perplexity filtering, encoding detection
- `output_filter.py` - Content moderation
- `hardening.py` - System prompt hardening
- `llm_judge.py` - LLM-as-a-judge for safety evaluation
- `hallucination.py` - Hallucination detection
- `injection_detector.py` - Prompt injection detection
- `orchestrator.py` - **NEW** Unified defense orchestration framework

### Evaluation Module (mox/evaluation/)

- `benchmarks.py` - HarmBench, AdvBench datasets
- `evaluator.py` - Attack/defense evaluation
- `judge.py` - **NEW** LLM Judge with PATTERN/SELF/EXTERNAL modes
- `redteam.py` - **UPGRADED** Red team orchestrator with advanced attack integration
- `framework.py` - **NEW** Unified evaluation framework

### API & UI

- **mox/api.py** - FastAPI endpoints at `/api/*`
- **mox/ui.py** - Gradio Web UI at `/ui/*`
- **mox/routes/** - API route modules
- **mox/cli.py** - CLI tool

## Key Patterns

### Creating an LLM Instance

```python
from mox.core.llm import OllamaLLM, OpenAILLM, AnthropicLLM, LLMFactory

# Local model (Ollama must be running)
llm = OllamaLLM(model="gemma3:4b", base_url="http://localhost:11434/v1")

# Or use factory
llm = LLMFactory.create_from_model_name("gpt-4")
```

### Running Red Team Tests

```python
from mox.evaluation import RedTeamOrchestrator
from mox.core.llm import OllamaLLM

target_llm = OllamaLLM(model="llama3")
attacker_llm = OllamaLLM(model="llama3")

orchestrator = RedTeamOrchestrator(attacker_llm, target_llm)

# Run scenarios (parallel or sequential)
results = await orchestrator.run_all_scenarios(parallel=True, max_concurrency=5)

# Generate reports
from mox.evaluation import RedTeamReportGenerator
RedTeamReportGenerator.save_report(results, "report.html", format="html")
```

### Using Unified Evaluator

```python
from mox.evaluation import UnifiedEvaluator, EvaluationType

evaluator = UnifiedEvaluator(target_llm)
evaluator.configure(parallel=True)

# Load scenarios
scenarios = evaluator.load_attack_scenarios("basic")
results = await evaluator.run(scenarios)
evaluator.save_report("report.html")
```

## Environment Variables

Create `.env` file:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MINIMAX_API_KEY=...
DEEPSEEK_API_KEY=...
COHERE_API_KEY=...
GROQ_API_KEY=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
SECRET_KEY=your-secret-key
MOX_REQUIRE_AUTH=false
```

## Testing with Local Models

Ollama must be running first:
```bash
ollama serve
ollama pull llama3  # or gemma3:4b, qwen3:4b, etc.
```

Then use in code:
```python
llm = OllamaLLM(model="llama3", base_url="http://localhost:11434/v1")
```
