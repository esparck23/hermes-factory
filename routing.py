from typing import Dict, Optional


def route_next(state: Dict, current_node: str) -> Optional[str]:
    """
    Decide el siguiente nodo en el flujo basado en el estado actual.
    
    Lógica:
    - Si el Quality Gate pasó, avanza al siguiente paso.
    - Si falló, va a diagnóstico (qoder) o reparación (vibe).
    - Si es el último paso, termina.
    """
    # Orden de ejecución estándar
    flow_order = [
        "qwen_scaffolding",
        "vibe_iteration", 
        "hermes_compiler",
        "qoder_diagnostics",
        "qoder_audit"
    ]
    
    # Si el Quality Gate pasó, avanza al siguiente nodo
    if state.get("quality_gate_passed"):
        try:
            current_index = flow_order.index(current_node)
            if current_index + 1 < len(flow_order):
                return flow_order[current_index + 1]
            else:
                return None  # Fin del flujo
        except ValueError:
            return None
    
    # Si falló, va a diagnóstico
    if current_node == "hermes_compiler":
        return "qoder_diagnostics"
    
    # Si qwen ya diagnosticó, vuelve a vibe para reparar
    if current_node == "qoder_diagnostics":
        return "vibe_iteration"
    
    # Tras pi_scaffolding (primer paso), avanzar a vibe_iteration
    # sin importar quality gate (el gate lo corre hermes_compiler después).
    if current_node == "qwen_scaffolding":
        return "vibe_iteration"
    
    # Tras vibe_iteration, avanzar a hermes_compiler (quien corre el quality gate).
    if current_node == "vibe_iteration":
        return "hermes_compiler"
    
    # Si vibe falló en reparación post-diagnóstico, volver a compilar
    return None


def router_quality_gate(state: Dict) -> str:
    if state.get("quality_gate_passed"):
        return "approved"
    if state.get("retry_count", 0) >= 3:
        return "human_interrupt"
    return "fix_with_qoder"
