from agently import Agently

from _shared import create_agent, print_action_results, print_response


ISSUE_PAYLOAD = {
    "title": "TriggerFlow stream stops after human approval",
    "body": (
        "After upgrading to 4.1, a TriggerFlow execution pauses for approval correctly, "
        "but after resume the runtime stream stops emitting chunk status updates. "
        "The workflow result is correct, but devtools cannot show the rest of the run."
    ),
    "labels": ["bug", "triggerflow", "devtools"],
    "comments": [
        "Reproduced with a two-step flow and async_continue_with.",
        "No issue when runtime stream is disabled.",
        "Expected stream events after approval resume.",
    ],
}


agent = create_agent(
    "deepseek",
    (
        "You are an issue processor for Agently. "
        "Use the managed_python_issue_metrics action for deterministic counting and scoring before replying. "
        "Do not invent metrics without calling the action."
    ),
    temperature=0.1,
)

agent.enable_python(
    action_id="managed_python_issue_metrics",
    desc=(
        "Run Python code inside a managed Python sandbox. "
        "Use it to calculate deterministic GitHub issue metrics from provided issue text and labels. "
        "Always assign the final metrics dict to `result`."
    ),
    expose_to_model=True,
)


if __name__ == "__main__":
    agent.use_actions("managed_python_issue_metrics")
    agent.input(
        {
            "task": (
                "Process this GitHub issue. First call managed_python_issue_metrics to compute: "
                "label_count, comment_count, whether TriggerFlow is involved, whether DevTools is involved, "
                "and a severity score where bug=3, triggerflow=2, devtools=1. "
                "The Python code must assign a dict to `result` with keys label_count, comment_count, "
                "triggerflow_involved, devtools_involved, and severity_score. "
                "Then reply with a triage summary, suggested owner, and next debugging step."
            ),
            "issue": ISSUE_PAYLOAD,
        }
    )

    records = agent.get_action_result()
    print_action_results(records)

    response = agent.get_response()
    print_response(response)

    print("[ACTION_CALL_HANDLES_AFTER_RELEASE]")
    print(Agently.execution_environment.list(scope="action_call"))
