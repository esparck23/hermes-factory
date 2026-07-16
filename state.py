from typing import Dict, List, TypedDict, Optional

Project = Dict[str, object]

class TeamState(TypedDict):
    project: Project
    project_prompt: str
    target_files: List[str]
    current_code_structure: Dict[str, str]
    last_execution_logs: str
    quality_gate_passed: bool
    retry_count: int
    error_diagnostics: Optional[str]
    final_report: str
    qoder_executed_in_this_run: bool
    run_id: Optional[str]
    attempt: int
    step: Optional[str]
    agent_context: Optional[Dict[str, Dict]] # Nuevo: Contexto estructurado por agente

