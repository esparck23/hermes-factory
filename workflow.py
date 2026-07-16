"""workflow.py — Orquestador universal de la Hermes A2A Factory.

Corre uno o muchos proyectos definidos en `active.yaml` usando
`projects.yaml` como catálogo. Cada proyecto tiene su propio `.harness/`.
"""
import re
import json as _json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

import yaml

from state import TeamState
from routing import route_next
from nodes import (
    node_pi_scaffolding,
    node_vibe_iteration,
    node_hermes_compiler,
    node_qwen_diagnostics,
    node_qoder_audit,
)


def _db_path() -> Path:
    return Path(__file__).parent / "state_checkpoint.db"


def _ensure_checkpoint_table() -> None:
    db = _db_path()
    try:
        import sqlite3
        with sqlite3.connect(db) as con:
            cur = con.cursor()
            # Tabla principal de transiciones
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    project_name TEXT,
                    step TEXT,
                    status TEXT,
                    summary TEXT,
                    transition_reason TEXT,
                    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
                )
                """
            )
            # Tabla de handovers entre agentes
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_handovers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    from_agent TEXT,
                    to_agent TEXT,
                    context_json TEXT,
                    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
                )
                """
            )
            con.commit()
    except Exception as exc:
        print("[HARNESS] No se pudo inicializar la base de datos: " + str(exc))


def _write_checkpoint(project: dict, state: dict, step: str) -> None:
    try:
        import sqlite3
        db = _db_path()
        run_id = state.get("run_id") or datetime.now().strftime("%Y%m%d%H%M%S")
        state["run_id"] = run_id
        state["step"] = step

        status = "success" if state.get("quality_gate_passed") else "failed"
        agent_context = state.get("agent_context", {})
        summary = ""
        if agent_context:
            last_agent = list(agent_context.keys())[-1]
            summary = agent_context.get(last_agent, {}).get("summary", "")[:500]
        
        reason = (state.get("error_diagnostics") or "")[:200] if status == "failed" else "Quality Gate Passed"

        with sqlite3.connect(db) as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO transitions (run_id, project_name, step, status, summary, transition_reason)
                VALUES (?,?,?,?,?,?)
                """,
                (run_id, project.get("name"), step, status, summary, reason),
            )
            con.commit()
    except Exception as exc:
        print("[HARNESS] No se pudo escribir checkpoint en la base de datos: " + str(exc))

def _write_handover(run_id: str, from_agent: str, to_agent: str, context: dict) -> None:
    try:
        import sqlite3
        import json
        db = _db_path()
        with sqlite3.connect(db) as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO agent_handovers (run_id, from_agent, to_agent, context_json) VALUES (?,?,?,?)",
                (run_id, from_agent, to_agent, json.dumps(context, ensure_ascii=False)),
            )
            con.commit()
    except Exception as exc:
        print("[HARNESS] No se pudo escribir handover: " + str(exc))

def _read_latest_checkpoint(project: dict):
    try:
        import sqlite3
        db = _db_path()
        with sqlite3.connect(db) as con:
            cur = con.cursor()
            cur.execute(
                "SELECT summary FROM transitions WHERE project_name=? ORDER BY id DESC LIMIT 1",
                (project.get("name"),),
            )
            row = cur.fetchone()
            if row:
                return {"summary": row[0]}
    except Exception:
        pass
    return None


def _extract_active_substep_block(root: Path):
    """Lee STAGES.md, extrae el bloque del Sub-paso activo y sus archivos objetivo.
    Genérico: funciona para cualquier etapa/proyecto que use .harness/STAGES.md.
    Retorna (sub_step, block_text, file_paths) o (None, '', set())."""
    stages_path = root / ".harness" / "STAGES.md"
    if not stages_path.exists():
        return None, "", set()
    content = stages_path.read_text(encoding="utf-8")
    active_match = re.search(r"Sub-paso activo:\s*(\d+\.\d+)", content)
    if not active_match:
        return None, "", set()
    sub_step = active_match.group(1)
    block_pattern = re.compile(
        r"(?:^|\n)" + re.escape(sub_step) + r"[^\n]*\n(.*?)(?:\n(?:\d+\.\d+|\*\*Etapa|\*\*BACKLOG)|\Z)",
        re.DOTALL,
    )
    block_match = block_pattern.search(content)
    if not block_match:
        return sub_step, "", set()
    block = block_match.group(1)
    file_paths = set()
    for line in block.splitlines():
        line_stripped = line.strip()
        for p in re.findall(r"`([^`]+)`", line_stripped):
            if re.match(r"^(src/|public/|tests?/)", p):
                file_paths.add(p.strip("`':;,.()[]{} "))
    return sub_step, block.strip(), file_paths


def _load_prompt(project: dict) -> str:
    root = Path(str(project.get("root", "") or "")).resolve()
    state_path = root / ".harness" / "STATE.md"
    objective = ""
    action = ""
    no_touch = ""
    stages_block = ""
    stages_files = set()
    try:
        content = state_path.read_text(encoding="utf-8")
        m = re.search(r"🔜 Sigue:\s*(.*)", content) or re.search(r"Próxima acción:\s*(.*)", content)
        if m:
            objective = m.group(1).strip()
        
        act = re.search(r"Acción:\s*(.*)", content, re.IGNORECASE)
        if act:
            action = act.group(1).strip()

        nt = re.search(r"No tocar:\s*(.*)", content, re.IGNORECASE)
        if nt:
            no_touch = nt.group(1).strip()
    except FileNotFoundError:
        pass
    
    # Extraer el bloque del Sub-paso activo de STAGES.md (genérico por etapa/proyecto)
    sub_step, stages_block, stages_files = _extract_active_substep_block(root)
    if sub_step and stages_block:
        action = (
            f"Implementar el sub-paso {sub_step} según el siguiente bloque de STAGES.md "
            f"(editar SOLO los archivos indicados):\n{stages_block}"
        )
    
    parts = []
    if action:
        parts.append("TAREA DIRECTA: " + action)
    if objective:
        parts.append("Contexto de lo que sigue: " + objective)
    if no_touch:
        parts.append("Restricción (No tocar): " + no_touch)
    if stages_files:
        parts.append("Archivos objetivo (desde STAGES.md): " + ", ".join(sorted(stages_files)))
    
    parts.append("Criterio de éxito: El código debe compilar, pasar tests y no tener errores de tipos.")
    return "\n".join(parts) if parts else "Desarrollar según el estado actual del proyecto."


def _merge_state_field(text: str, key_pattern: str, value: str) -> str:
    placeholders = {
        "salud": "🟢", "hecho": "Hecho:", "sigue": "🔜", "riesgo": "⚠️", "preview": "🔗", "accion": "¿Acción tuya?"
    }
    lowered = key_pattern.lower()
    for name, token in placeholders.items():
        if lowered.startswith(name) or lowered in name:
            key_pattern = token + ".*"
            break
    pattern = re.compile(r"(" + re.escape(key_pattern.split(":")[0]) + r"[^\n]*:[ \t]*)([^\n]*)", re.IGNORECASE)
    replacement = r"\1" + value
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text + chr(10) + replacement


def _write_state(project: dict, state: TeamState) -> None:
    root = Path(str(project.get("root", "") or "")).resolve()
    state_path = root / ".harness" / "STATE.md"
    try:
        original = state_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        original = ""
    gate = "PASSED" if state.get("quality_gate_passed") else "FAILED"
    action = "NO" if state.get("quality_gate_passed") else "SÍ"
    risk = state.get("error_diagnostics") or "Sin bloqueos confirmados en esta corrida."
    report = state.get("final_report", "Pipeline ejecutado.")

    updated = original
    updated = _merge_state_field(updated, "🟢 Salud:", "🟢 Salud: Verde")
    updated = _merge_state_field(updated, "Hecho:", report)
    updated = _merge_state_field(updated, "🔜 Sigue:", "Próxima iteración desde prompt cargado.")
    updated = _merge_state_field(updated, "⚠️ Riesgo:", str(risk))
    updated = _merge_state_field(updated, "🔗 Preview:", "./sandbox (Quality Gate " + gate + ")")
    updated = _merge_state_field(updated, "¿Acción tuya?:", action)
    try:
        state_path.write_text(updated, encoding="utf-8")
    except Exception as exc:
        print("[HARNESS] No se pudo escribir STATE.md: " + str(exc))


def _write_journal(project: dict, quality_passed: bool) -> None:
    root = Path(str(project.get("root", "") or "")).resolve()
    journal_path = root / ".harness" / "JOURNAL.md"
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    entry = "### " + fecha_hoy + " — Ejecución Automática Factory" + chr(10)
    entry += "- Pipeline ejecutado de inicio a fin de forma nativa." + chr(10)
    entry += "- Control de calidad: " + ("Aprobado" if quality_passed else "Fallado") + "." + chr(10)
    try:
        current = journal_path.read_text(encoding="utf-8") if journal_path.exists() else ""
        journal_path.write_text(current + chr(10) + entry, encoding="utf-8")
    except Exception as exc:
        print("[HARNESS] No se pudo escribir JOURNAL.md: " + str(exc))


def _write_blocker(project: dict, title: str, body: str) -> None:
    root = Path(str(project.get("root", "") or "")).resolve()
    blockers_path = root / ".harness" / "BLOCKERS.md"
    text = "### " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " — " + title + chr(10) + body + chr(10)
    try:
        current = blockers_path.read_text(encoding="utf-8") if blockers_path.exists() else ""
        blockers_path.write_text(current + chr(10) + text, encoding="utf-8")
    except Exception as exc:
        print("[HARNESS] No se pudo escribir BLOCKERS.md: " + str(exc))


def _file_changed_vs_main(file_path, root):
    try:
        rel = file_path.relative_to(root).as_posix()
        proc = subprocess.run(
            ["git", "diff", "origin/main", "--", rel],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if proc.stdout.strip():
            return True
        proc2 = subprocess.run(
            ["git", "diff", "--name-only", "origin/main", "--", rel],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if proc2.stdout.strip():
            return True
        if file_path.exists():
            proc3 = subprocess.run(
                ["git", "ls-files", "--error-unmatch", rel],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            return proc3.returncode != 0
        return False
    except Exception:
        return False


def _verify_objective(project, state):
    root = Path(str(project.get("root", "") or "")).resolve()
    stages_path = root / ".harness" / "STAGES.md"
    if not stages_path.exists():
        return False, "STAGES.md not found"

    content = stages_path.read_text(encoding="utf-8")
    active_match = re.search(r"Sub-paso activo:\s*(\d+\.\d+)", content)
    if not active_match:
        return False, "No active sub-step found"

    sub_step = active_match.group(1)
    block_pattern = re.compile(
        r"(?:^|\n)" + re.escape(sub_step) + r"[^\n]*\n(.*?)(?:\n(?:\d+\.\d+|\*\*Etapa|\*\*BACKLOG)|\Z)",
        re.DOTALL,
    )
    block_match = block_pattern.search(content)
    if not block_match:
        return False, "Sub-step %s block not found" % sub_step

    block = block_match.group(1)
    paths = set()
    raw_paths = set()
    modify_candidates = set()
    modify_modifiers = ["extiende", "modificar", "completa", "implementar", "implementa", "crear", "crea"]
    for line in block.splitlines():
        line_stripped = line.strip()
        for p in re.findall(r"`([^`]+)`", line_stripped):
            paths.add(p)
        for p in re.findall(r"(src/[^\s`,;]+|public/[^\s`,;]+|tests?/[^\s`,;]+)", line_stripped):
            raw_paths.add(p)

    paths = {p.strip("`':;,.()[]{} ") for p in paths if re.match(r"^(src/|public/|tests?/)", p)}
    for p in raw_paths:
        cp = re.sub(r"[:;,.()\[\]{}]+$", "", p)
        if re.match(r"^[A-Za-z0-9_./-]+$", cp):
            paths.add(cp)

    line_modifies = {}
    for line in block.splitlines():
        for p in re.findall(r"(src/[^\s`,;]+|public/[^\s`,;]+|tests?/[^\s`,;]+)", line):
            cp = re.sub(r"[:;,.()\[\]{}]+$", "", p)
            if re.match(r"^[A-Za-z0-9_./-]+$", cp):
                line_modifies[cp] = line_modifies.get(cp, False) or any(m in line.lower() for m in modify_modifiers + ["extiende", "modifica", "modificar", "completa", "implementar"])

    missing = []
    for p in sorted(paths):
        if not (root / p).exists():
            missing.append("Missing file: %s" % p)

    for p, must_change in line_modifies.items():
        if not must_change:
            continue
        fp = root / p
        if fp.exists():
            changed = _file_changed_vs_main(fp, root)
            if not changed:
                missing.append("No changes detected vs origin/main: %s" % p)

    if missing:
        return False, "BLK-008 objective not met: " + "; ".join(missing)
    return True, "Objective verified"


def run_for_project(project: dict) -> None:
    root = Path(str(project.get("root", "") or "")).resolve()
    prompt = _load_prompt(project)
    if not prompt:
        print("[HARNESS] No hay acción activa en STATE.md de " + str(project.get("name")))
        return

    state: TeamState = {
        "project": project,
        "project_prompt": prompt,
        "target_files": [],
        "current_code_structure": {},
        "quality_gate_passed": False,
        "error_diagnostics": None,
        "final_report": "",
        "retry_count": 0,
        "agent_context": {},
    }

    _ensure_checkpoint_table()
    current_node = "pi_scaffolding"
    
    # Orquestación simplificada tipo grafo artesanal
    nodes = {
        "pi_scaffolding": node_pi_scaffolding,
        "vibe_iteration": node_vibe_iteration,
        "hermes_compiler": node_hermes_compiler,
        "qwen_diagnostics": node_qwen_diagnostics,
        "qoder_audit": node_qoder_audit,
    }

    visited = []
    while current_node and len(visited) < 15:
        visited.append(current_node)
        print(f"\n[HARNESS] Ejecutando Nodo: {current_node}")
        
        node_func = nodes.get(current_node)
        if not node_func:
            break
            
        # Ejecutar nodo
        state = node_func(state)
        
        # Registrar checkpoint de transición
        _write_checkpoint(project, state, current_node)
        
        # Decidir siguiente nodo
        next_node = route_next(state, current_node)
        
        if next_node:
            # Handover si hay cambio de agente
            if next_node != current_node:
                ctx = state.get("agent_context", {}).get(current_node, {})
                _write_handover(state.get("run_id"), current_node, next_node, ctx)
        
        current_node = next_node

    # Post-proceso: Actualizar Arneses
    obj_met, obj_msg = _verify_objective(project, state)
    state["quality_gate_passed"] = state.get("quality_gate_passed", False) and obj_met
    if not obj_met:
        state["error_diagnostics"] = (state.get("error_diagnostics") or "") + " | Objective failed: " + obj_msg

    _write_state(project, state)
    _write_journal(project, state["quality_gate_passed"])
    if not state["quality_gate_passed"]:
        _write_blocker(project, "Fallo en Calidad/Objetivo", state.get("error_diagnostics") or "Error desconocido")

    print(f"\n[HARNESS] Ciclo completado para {project.get('name')}. Calidad: {state['quality_gate_passed']}")


def main():
    _ensure_checkpoint_table()
    active_path = Path(__file__).parent / "active.yaml"
    projects_path = Path(__file__).parent / "projects.yaml"

    if not active_path.exists() or not projects_path.exists():
        print("Faltan archivos de configuración.")
        return

    active = yaml.safe_load(active_path.read_text())
    catalog = yaml.safe_load(projects_path.read_text())
    
    project_names = active.get("active_projects", []) or active.get("active", [])
    projects_list = catalog.get("projects", [])
    # Soporta projects como lista (buscar por name) o como dict.
    if isinstance(projects_list, dict):
        catalog_projects = projects_list
    else:
        catalog_projects = {p.get("name"): p for p in projects_list if isinstance(p, dict)}
    for name in project_names:
        p_data = catalog_projects.get(name)
        if p_data:
            print(f"\n=== Iniciando Factory para: {name} ===")
            run_for_project(p_data)
        else:
            print(f"Proyecto {name} no encontrado en catálogo.")

if __name__ == "__main__":
    main()
