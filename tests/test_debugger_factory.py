# test score function

from logikon.debuggers.base import AbstractArtifactDebugger, AbstractDebugger, AbstractScoreDebugger
from logikon.debuggers.factory import DebuggerFactory, get_debugger_registry
from logikon.schemas.configs import DebugConfig


def test_debugger_factory():
    registry = get_debugger_registry()

    for product_kw, debugger_classes in registry.items():
        for debugger_class in debugger_classes:
            print(f"Testing: {product_kw}: {debugger_class}")
            artifacts = []
            metrics = []
            if issubclass(debugger_class, AbstractArtifactDebugger):
                artifacts.append(product_kw)
            elif issubclass(debugger_class, AbstractScoreDebugger):
                metrics.append(product_kw)
            else:
                print("Unknown debugger class type")
                raise AssertionError()

            config = DebugConfig(metrics=metrics, artifacts=artifacts)

            debug_chain = DebuggerFactory().create(config)
            assert isinstance(debug_chain, AbstractDebugger)

            # loop over chain to debugger that produces product
            current_debugger = debug_chain
            while current_debugger.get_product() != product_kw:
                current_debugger = current_debugger._next_debugger
                assert current_debugger

def test_debugger_factory2():
    config = DebugConfig(
        expert_model="text-ada-002",
        llm_framework="VLLM",
    )
    debug_chain = DebuggerFactory().create(config)
    assert isinstance(debug_chain, AbstractDebugger)
