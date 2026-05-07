from agently import Agently

from _shared import create_agent, print_action_results, print_response


agent = create_agent(
    "ollama",
    (
        "You are an exact calculation assistant. "
        "When a managed action is available, call it before replying. "
        "Do not calculate list statistics by yourself. "
        "Do not include URLs or source links in the reply."
    ),
)

agent.enable_python(
    action_id="managed_python_stats",
    desc=(
        "Run Python code inside a managed Python sandbox. "
        "Use it for exact arithmetic and list statistics. "
        "Always assign the final answer to a variable named `result`."
    ),
    expose_to_model=True,
)


if __name__ == "__main__":
    agent.use_actions("managed_python_stats")
    agent.input(
        "Use the managed_python_stats action to run Python code for this list: [15, 23, 42, 8, 12]. "
        "Calculate average, count, and max-minus-min gap. "
        "The Python code must assign a dict to `result` with keys average, count, and max_minus_min_gap. "
        "Then reply with those values."
    )

    records = agent.get_action_result()
    print_action_results(records)

    response = agent.get_response()
    print_response(response)

    print("[ACTION_CALL_HANDLES_AFTER_RELEASE]")
    print(Agently.execution_environment.list(scope="action_call"))
