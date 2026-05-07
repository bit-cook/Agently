# Execution Environment Examples

These examples show how Execution Environment prepares managed runtime
dependencies for Actions and TriggerFlow.

Example groups:

- `01_action_python_environment_local.py`
  - Runs without any model API key.
  - Executes a Python sandbox action directly through `Agently.action`.
  - Verifies that the `action_call` scoped environment is released after the call.
- `02_agent_python_environment_ollama.py`
  - Uses an Ollama OpenAI-compatible endpoint.
  - Defaults to `qwen2.5:7b`, which is sufficient for the small action-selection task.
  - Uses `agent.enable_python(...)` so app code does not hand-write executor or environment declarations.
  - Lets the model choose the managed Python action, then prints action records and the final reply.
- `03_agent_issue_processor_deepseek.py`
  - Uses DeepSeek for a more complex issue-processing prompt.
  - Uses `agent.enable_python(...)` for deterministic issue metrics before replying.
- `04_triggerflow_python_environment_local.py`
  - Runs without any model API key.
  - Injects a managed Python sandbox into TriggerFlow `runtime_resources`.
  - Verifies that the execution-scoped handle is released when the execution closes.

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
- Action dispatch ensures required environments immediately before executor calls.
- `action_call` scoped handles are released after the action call.
- TriggerFlow still exposes live resources through `runtime_resources`; managed resources are injected by Execution Environment and released when the execution closes.
