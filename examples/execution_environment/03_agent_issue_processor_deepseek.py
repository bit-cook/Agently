from typing import Any, cast

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


class ManagedIssueMetricsExecutor:
    kind = "managed_python_issue_metrics"
    sandboxed = True

    async def execute(self, *, spec, action_call, policy, settings):
        _ = (spec, policy, settings)
        action_input = action_call.get("action_input", {})
        if not isinstance(action_input, dict):
            action_input = {}
        issue = action_input.get("issue", {})
        if not isinstance(issue, dict):
            issue = {}

        title = str(issue.get("title", ""))
        body = str(issue.get("body", ""))
        labels = [str(label).lower() for label in issue.get("labels", []) if isinstance(label, str)]
        comments = [str(comment) for comment in issue.get("comments", [])]
        text = " ".join([title, body, *comments]).lower()

        resources = action_call.get("execution_environment_resources", {})
        sandbox = cast(dict[str, Any], resources).get("managed_python_issue_metrics")
        if sandbox is None or not hasattr(sandbox, "run"):
            raise RuntimeError("managed_python_issue_metrics execution environment is not available.")

        return sandbox.run(
            "labels = " + repr(labels) + "\n"
            "comments = " + repr(comments) + "\n"
            "text = " + repr(text) + "\n"
            "severity_score = 0\n"
            "if 'bug' in labels:\n"
            "    severity_score = severity_score + 3\n"
            "if 'triggerflow' in labels or 'triggerflow' in text:\n"
            "    severity_score = severity_score + 2\n"
            "if 'devtools' in labels or 'devtools' in text:\n"
            "    severity_score = severity_score + 1\n"
            "result = {\n"
            "    'label_count': len(labels),\n"
            "    'comment_count': len(comments),\n"
            "    'triggerflow_involved': ('triggerflow' in labels) or ('triggerflow' in text),\n"
            "    'devtools_involved': ('devtools' in labels) or ('devtools' in text),\n"
            "    'severity_score': severity_score,\n"
            "}\n"
        )["result"]


agent = create_agent(
    "deepseek",
    (
        "You are an issue processor for Agently. "
        "Use the managed_python_issue_metrics action for deterministic counting and scoring before replying. "
        "Do not invent metrics without calling the action."
    ),
    temperature=0.1,
)

agent.action.register_action(
    action_id="managed_python_issue_metrics",
    desc=(
        "Calculate deterministic GitHub issue metrics by using a managed Python execution environment."
    ),
    kwargs={"issue": (dict, "GitHub issue payload with title, body, labels, and comments.")},
    executor=ManagedIssueMetricsExecutor(),
    side_effect_level="exec",
    sandbox_required=True,
    expose_to_model=True,
    execution_environments=[
        {
            "kind": "python",
            "scope": "action_call",
            "resource_key": "managed_python_issue_metrics",
        }
    ],
)


if __name__ == "__main__":
    agent.use_actions("managed_python_issue_metrics")
    agent.input(
        {
            "task": (
                "Process this GitHub issue. First call managed_python_issue_metrics to compute: "
                "label_count, comment_count, whether TriggerFlow is involved, whether DevTools is involved, "
                "and a severity score where bug=3, triggerflow=2, devtools=1. "
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
