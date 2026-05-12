# Execution Environment Examples

These examples show the recommended developer path for managed execution
capabilities.

Most application code should start with `agent.enable_*` helpers. They hide the
core manager/provider lifecycle and expose model-callable Actions with sensible
defaults.

## Start Here

| File | Audience | What it shows |
|---|---|---|
| `01_action_python_environment_local.py` | App developers, no model required | Enable a managed Python action with `agent.enable_python(...)` and call it directly for a deterministic local check. |
| `02_agent_python_environment_ollama.py` | App developers with local Ollama | Let a model decide to call the enabled Python action before replying. |
| `03_agent_issue_processor_deepseek.py` | App developers with DeepSeek | A realistic issue-triage task where the model uses Python for deterministic metrics and then writes the summary. |
| `04_triggerflow_python_environment_local.py` | Workflow/framework developers | Inject a managed Python sandbox into TriggerFlow `runtime_resources`. |

## Copy-Paste Shape

For application developers, the shape is intentionally small:

```python
agent = Agently.create_agent()
agent.enable_python(desc="Use for exact calculations. Assign the final answer to `result`.")

agent.input("Use Python to calculate the average of [15, 23, 42, 8, 12].")
records = agent.get_action_result()
response = agent.get_response()
```

You normally do not need to call `Agently.execution_environment` directly. The
Action dispatcher ensures and releases the managed environment when the enabled
action is called.

## Example Details

- `01_action_python_environment_local.py`
  - Runs without any model API key.
  - Uses `agent.enable_python(...)`, then calls the registered action directly.
  - Good for verifying the local package without a model endpoint.
- `02_agent_python_environment_ollama.py`
  - Uses an Ollama OpenAI-compatible endpoint.
  - Defaults to `qwen2.5:7b`, which is sufficient for the small action-selection task.
  - Lets the model choose the managed Python action, then prints action records and the final reply.
- `03_agent_issue_processor_deepseek.py`
  - Uses DeepSeek for a more complex issue-processing prompt.
  - Shows that execution is real: model planning calls the Python action, the sandbox computes metrics, and the final reply uses those action results.
- `04_triggerflow_python_environment_local.py`
  - Runs without any model API key.
  - Injects a managed Python sandbox into TriggerFlow `runtime_resources`.
  - This is intentionally lower-level than the first three examples.

Before running the Ollama example, make sure Ollama is running and the model is
available:

```bash
ollama pull qwen2.5:7b
```

Optional Ollama environment variables:

- `OLLAMA_BASE_URL`, defaults to `http://localhost:11434/v1`
- `OLLAMA_DEFAULT_MODEL`, defaults to `qwen2.5:7b`

Before running the DeepSeek example, set:

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`, optional, defaults to `https://api.deepseek.com/v1`
- `DEEPSEEK_DEFAULT_MODEL`, optional, defaults to `deepseek-chat`

Run:

```bash
python examples/execution_environment/01_action_python_environment_local.py
python examples/execution_environment/02_agent_python_environment_ollama.py
python examples/execution_environment/03_agent_issue_processor_deepseek.py
python examples/execution_environment/04_triggerflow_python_environment_local.py
```

Notes:

- Execution Environment declarations are lazy; a declaration does not start a sandbox or transport.
- Business examples should prefer `agent.enable_python(...)`, `agent.enable_shell(...)`, and `agent.enable_workspace(...)` over direct manager/provider APIs.
- `enable_*` helpers provide default action descriptions, so `desc=` is optional. By default `desc=` appends extra guidance; `desc_mode="override"` replaces the default description only when you need full control.
- Action dispatch ensures required environments immediately before executor calls.
- `action_call` scoped handles are released after the action call.
- TriggerFlow still exposes live resources through `runtime_resources`; managed resources are injected by Execution Environment and released when the execution closes.
