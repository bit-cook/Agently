import pytest
from typing import Any, cast

from agently import Agently
from agently.core import ExecutionEnvironmentApprovalRequired, ExecutionEnvironmentManager
from agently.types.data import ExecutionEnvironmentRequirement
from agently.utils import Settings


def _create_manager():
    settings = Settings(name="ExecutionEnvironmentTestSettings", parent=Agently.settings)
    return ExecutionEnvironmentManager(
        plugin_manager=Agently.plugin_manager,
        settings=settings,
        event_center=Agently.event_center,
    )


def test_execution_environment_declare_is_lazy():
    manager = _create_manager()
    requirement = manager.declare(
        {
            "kind": "python",
            "scope": "action_call",
            "resource_key": "python_test",
        }
    )

    assert requirement["kind"] == "python"
    assert manager.list() == []


@pytest.mark.asyncio
async def test_execution_environment_ensure_reuses_and_releases_handle():
    manager = _create_manager()
    requirement = cast(ExecutionEnvironmentRequirement, {
        "kind": "python",
        "scope": "session",
        "owner_id": "session-1",
        "resource_key": "python_test",
        "config": {"base_vars": {"value": 1}},
    })

    handle_1 = await manager.async_ensure(requirement)
    handle_2 = await manager.async_ensure(requirement)

    assert handle_1.get("handle_id") == handle_2.get("handle_id")
    assert handle_2.get("ref_count") == 2

    await manager.async_release(handle_1)
    assert manager.list()[0].get("ref_count") == 1
    await manager.async_release(handle_2)
    assert manager.list() == []


@pytest.mark.asyncio
async def test_execution_environment_approval_required_does_not_start():
    manager = _create_manager()

    with pytest.raises(ExecutionEnvironmentApprovalRequired):
        await manager.async_ensure(
            {
                "kind": "python",
                "scope": "action_call",
                "resource_key": "python_test",
                "approval_required": True,
            }
        )

    assert manager.list() == []


def test_action_python_sandbox_uses_execution_environment():
    action_id = "python_env_action"
    Agently.action.register_python_sandbox_action(action_id=action_id, expose_to_model=False)

    result = Agently.action.execute_action(action_id, {"python_code": "result = 40 + 2"})

    assert result.get("status") == "success"
    result_data = cast(dict[str, Any], result.get("data"))
    assert result_data["result"] == 42
    assert Agently.execution_environment.list(scope="action_call") == []


def test_action_bash_sandbox_uses_execution_environment(tmp_path):
    action_id = "bash_env_action"
    Agently.action.register_bash_sandbox_action(
        action_id=action_id,
        expose_to_model=False,
        allowed_cmd_prefixes=["pwd"],
        allowed_workdir_roots=[str(tmp_path)],
    )

    result = Agently.action.execute_action(action_id, {"cmd": "pwd", "workdir": str(tmp_path)})

    assert result.get("status") == "success"
    result_data = cast(dict[str, Any], result.get("data"))
    assert result_data["ok"] is True
    assert str(tmp_path) in result_data["stdout"]
    assert Agently.execution_environment.list(scope="action_call") == []


def test_action_environment_approval_returns_action_result():
    action_id = "approval_env_action"
    Agently.action.register_python_sandbox_action(action_id=action_id, expose_to_model=False)
    spec = Agently.action.action_registry.get_spec(action_id)
    assert spec is not None
    spec.get("execution_environments", [])[0]["approval_required"] = True

    result = Agently.action.execute_action(action_id, {"python_code": "result = 1"})

    assert result.get("status") == "approval_required"
    approval = cast(dict[str, Any], result.get("approval"))
    assert approval["required"] is True


@pytest.mark.asyncio
async def test_custom_action_executor_signature_still_works():
    action_id = "custom_executor_env_compat"

    class EchoExecutor:
        kind = "echo"
        sandboxed = False

        async def execute(self, *, spec, action_call, policy, settings):
            return {
                "spec": spec["action_id"],
                "input": action_call["action_input"],
                "policy": policy,
                "settings": settings.name,
            }

    Agently.action.register_action(
        action_id=action_id,
        desc="Compatibility executor.",
        kwargs={"value": (int, "")},
        executor=EchoExecutor(),
        expose_to_model=False,
    )

    result = await Agently.action.async_execute_action(action_id, {"value": 7})

    assert result.get("status") == "success"
    result_data = cast(dict[str, Any], result.get("data"))
    assert result_data["spec"] == action_id
    assert result_data["input"] == {"value": 7}
