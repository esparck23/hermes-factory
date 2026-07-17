import os
import sys
import re
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde .env si existe
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
import json
import re
import subprocess
import glob
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from state import TeamState

NODE_TIMEOUT = 180

def validate_cli_paths() -> dict:
    """Validar rutas de CLIs de .env o usar los valores por defecto si existen, con fallback a comandos básicos."""
    defaults = {
        "qwen": r"C:\Users\Agent\AppData\Roaming\npm\qwen.cmd",
        "vibe": r"C:\Users\Agent\.local\bin\vibe.exe",
        "qodercli": r"C:\Users\Agent\.qoder\bin\qodercli\qodercli.exe",
        "pi": r"C:\Users\Agent\AppData\Roaming\npm\pi.cmd",
    }
    
    cli_paths = {}
    for name in ["qwen", "vibe", "qodercli", "pi"]:
        env_val = os.getenv(f"CLI_{name.upper()}")
        if env_val:
            # Si el valor incluye un comando (ej: "python script.py"), validar el script
            if " " in env_val:
                # Extraer la ruta del script (último componente)
                script_path = env_val.split()[-1]
                if Path(script_path).exists():
                    cli_paths[name] = env_val
                else:
                    print(f"[WARNING] La ruta de entorno CLI_{name.upper()} no existe: '{env_val}'. Usando fallback.")
                    if Path(defaults[name]).exists():
                        cli_paths[name] = defaults[name]
                    else:
                        cli_paths[name] = name
            else:
                # Es una ruta directa
                if Path(env_val).exists():
                    cli_paths[name] = env_val
                else:
                    print(f"[WARNING] La ruta de entorno CLI_{name.upper()} no existe: '{env_val}'. Usando fallback.")
                    if Path(defaults[name]).exists():
                        cli_paths[name] = defaults[name]
                    else:
                        cli_paths[name] = name
        else:
            if Path(defaults[name]).exists():
                cli_paths[name] = defaults[name]
            else:
                cli_paths[name] = name
                
    return cli_paths


def validate_extra_paths() -> list:
    """Validar paths adicionales definidos en CLI_EXTRA_PATHS o defaults."""
    default_extras = [
        r"C:\Users\Agent\AppData\Roaming\npm",
        r"C:\Users\Agent\.local\bin",
    ]
    
    env_val = os.getenv("CLI_EXTRA_PATHS")
    if env_val:
        paths = [p.strip() for p in env_val.split(";") if p.strip()]
    else:
        paths = default_extras
        
    valid_paths = []
    for path in paths:
        if Path(path).exists():
            valid_paths.append(path)
        else:
            print(f"[WARNING] Path adicional no existe y se ignora: '{path}'")
    return valid_paths


CLI_PATHS = validate_cli_paths()
EXTRA_PATHS = validate_extra_paths()
# Removed old EXTRA_PATHS and CLI_PATHS definitions


def _with_extended_env() -> dict:
    env = os.environ.copy()
    path = env.get("PATH", "")
    for extra in EXTRA_PATHS:
        if extra and extra not in path:
            env["PATH"] = extra + os.pathsep + path
    return env


def _with_vibe_env() -> dict:
    """Entorno específico para Vibe: preserva PYTHONPATH y añade paths adicionales."""
    env = os.environ.copy()
    path = env.get("PATH", "")
    for extra in EXTRA_PATHS:
        if extra and extra not in path:
            env["PATH"] = extra + os.pathsep + path
    # NO eliminamos PYTHONPATH para Vibe
    return env


def _resolve_cmd(cmd: List[str]) -> List[str]:
    import shlex
    resolved = []
    for c in cmd:
        if c in CLI_PATHS:
            cli_value = CLI_PATHS[c]
            try:
                # shlex.split con posix=False maneja correctamente rutas de Windows con espacios y comillas
                split_cmd = shlex.split(cli_value, posix=False)
                resolved.extend(split_cmd)
            except Exception:
                last_space_idx = cli_value.rfind(' ')
                if last_space_idx != -1:
                    executable = cli_value[:last_space_idx]
                    script = cli_value[last_space_idx + 1:]
                    resolved.extend([executable, script])
                else:
                    resolved.append(cli_value)
        else:
            resolved.append(c)
    return resolved


def _project_path(state: TeamState, default: str = ".") -> Path:
    project = state.get("project", {})
    root = project.get("root", default)
    return Path(str(root)).resolve()


def _run_cli(cmd: List[str], cwd: Path) -> str:
    try:
        proc = subprocess.run(
            _resolve_cmd(cmd),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            timeout=NODE_TIMEOUT,
            env=_with_extended_env(),
        )
        return proc.stdout + "\n" + proc.stderr
    except subprocess.TimeoutExpired:
        return "CLI Timeout"
    except Exception as e:
        return f"CLI Error: {str(e)}"


def _atomic_write(project_root: Path, files: Dict[str, str]) -> TeamState:
    state: TeamState = {"current_code_structure": {}}
    for file_path, content in files.items():
        full_path = project_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            full_path.write_text(content, encoding="utf-8")
            state["current_code_structure"][file_path] = content
        except Exception as exc:
            print(f"[HERMES LOG] No se pudo escribir {file_path}: {exc}")
    return state


def node_qwen_scaffolding(state: TeamState) -> TeamState:
    print("[HERMES LOG] Invocando a Pi para scaffolding inicial...")
    project_root = _project_path(state, ".")
    prompt = state.get("project_prompt") or "Desarrollar componentes según el estado actual."
    
    # Añadir contexto de STATE.md al prompt del sistema para el agente
    state_path = project_root / ".harness" / "STATE.md"
    state_content = ""
    if state_path.exists():
        state_content = state_path.read_text(encoding="utf-8")

    full_prompt = (
        f"Eres un agente de scaffolding (pi). Tu tarea es ejecutar la acción definida en el arnés.\n"
        f"Contexto del proyecto (STATE.md):\n{state_content}\n\n"
        f"Instrucción específica: {prompt}"
    )

    cmd = [
        "pi",
        "--mode", "json",
        "--no-session",
        "-p", full_prompt,
    ]
    try:
        proc = subprocess.run(_resolve_cmd(cmd), cwd=str(project_root), capture_output=True, text=True, check=False, timeout=300, env=_with_extended_env())
    except subprocess.TimeoutExpired:
        state["last_execution_logs"] = "Qwen timeout (5 min)"
        state["error_diagnostics"] = "timeout: Qwen no completó la tarea en 5 minutos"
        state.setdefault("retry_count", 0)
        state["retry_count"] += 1
        return state
    
    stdout = proc.stdout
    state["last_execution_logs"] = stdout + "\n" + proc.stderr
    
    # Extraer resumen para el handover estructurado
    summary = "Scaffolding completado."
    # Intentar buscar un campo summary en el JSON de salida de pi si existe
    m = re.search(r"\"summary\":\s*\"(.*?)\"", stdout)
    if m: summary = m.group(1)
    
    # Registrar contexto del agente para observabilidad y handovers
    state["agent_context"] = state.get("agent_context", {})
    state["agent_context"]["pi_scaffolding"] = {
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }
    
    return state


def node_vibe_iteration(state: TeamState) -> TeamState:
    print("[HERMES LOG] Invocando a Vibe para iteración de código...")
    project_root = _project_path(state, ".")
    prompt = state.get("project_prompt") or "Pule el código y asegura que pase Quality Gate."
    
    # Contexto de STATE.md
    state_path = project_root / ".harness" / "STATE.md"
    state_content = ""
    if state_path.exists():
        state_content = state_path.read_text(encoding="utf-8")

    full_prompt = (
        f"Eres un agente de iteración de código (vibe). Tu tarea es pulir el código según el arnés.\n"
        f"Contexto del proyecto (STATE.md):\n{state_content}\n\n"
        f"Instrucción específica: {prompt}"
    )

    cmd = [
        "vibe",
        "--mode", "json",
        "-p", full_prompt,
    ]
    try:
        proc = subprocess.run(_resolve_cmd(cmd), cwd=str(project_root), capture_output=True, text=True, check=False, timeout=300, env=_with_vibe_env())
    except subprocess.TimeoutExpired:
        state["last_execution_logs"] = "Vibe timeout (5 min)"
        state["error_diagnostics"] = "timeout: Vibe no completó la tarea en 5 minutos"
        state.setdefault("retry_count", 0)
        state["retry_count"] += 1
        return state
    
    stdout = proc.stdout
    state["last_execution_logs"] = stdout + "\n" + proc.stderr
    
    # Extraer resumen
    summary = "Iteración de código completada."
    m = re.search(r"\"summary\":\s*\"(.*?)\"", stdout)
    if m: summary = m.group(1)
    
    # Registrar contexto del agente
    state["agent_context"] = state.get("agent_context", {})
    state["agent_context"]["vibe_iteration"] = {
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }
    
    return state


def node_hermes_compiler(state: TeamState) -> TeamState:
    print("[HERMES LOG] Compilando con Hermes Compiler...")
    project_root = _project_path(state, ".")
    
    # Ejecutar comando de compilación según el tipo de proyecto
    if (project_root / "pyproject.toml").exists():
        cmd = [sys.executable, "-m", "pytest", "-q"]
    elif (project_root / "package.json").exists():
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        cmd = [npm_cmd, "run", "build"]
    else:
        py_files = list(project_root.rglob("*.py"))
        if py_files:
            cmd = [sys.executable, "-m", "py_compile"] + [str(f) for f in py_files[:50]]
        else:
            state["quality_gate_passed"] = True
            state["agent_context"].setdefault("hermes_compiler", {})["summary"] = "Sin artefactos compilables."
            return state
    
    stdout = ""
    stderr = ""
    try:
        proc = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, check=False, timeout=300, env=_with_extended_env())
        stdout = proc.stdout
        stderr = proc.stderr
        
        if proc.returncode == 0:
            state["quality_gate_passed"] = True
            summary = "Compilación exitosa."
        else:
            state["quality_gate_passed"] = False
            state["error_diagnostics"] = f"Compilation failed: {stderr}"
            summary = "Fallo en compilación."
    except Exception as e:
        state["quality_gate_passed"] = False
        state["error_diagnostics"] = f"Compilation error: {str(e)}"
        summary = "Error en compilación."
    
    state["last_execution_logs"] = stdout + "\n" + stderr
    
    # Registrar contexto del agente
    state["agent_context"] = state.get("agent_context", {})
    state["agent_context"]["hermes_compiler"] = {
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }
    
    return state


def node_qoder_diagnostics(state: TeamState) -> TeamState:
    print("[HERMES LOG] Ejecutando diagnóstico con Qoder (qwen role)...")
    project_root = _project_path(state, ".")
    prompt = state.get("project_prompt") or "Diagnostica el error y sugiere soluciones."
    
    # Contexto de STATE.md
    state_path = project_root / ".harness" / "STATE.md"
    state_content = ""
    if state_path.exists():
        state_content = state_path.read_text(encoding="utf-8")

    full_prompt = (
        f"Eres un agente de diagnóstico (qwen). Analiza el error y sugiere soluciones.\n"
        f"Contexto del proyecto (STATE.md):\n{state_content}\n\n"
        f"Error detectado: {state.get('error_diagnostics', 'Ninguno')}\n\n"
        f"Instrucción específica: {prompt}"
    )

    cmd = [
        "pi",
        "--mode", "json",
        "--max-session-turns", "8",
        "--max-tool-calls", "30",
        "--max-wall-time", "10m",
        "-p", full_prompt,
    ]
    try:
        proc = subprocess.run(_resolve_cmd(cmd), cwd=str(project_root), capture_output=True, text=True, check=False, timeout=300, env=_with_extended_env())
    except subprocess.TimeoutExpired:
        state["last_execution_logs"] = "Qwen timeout (5 min)"
        state["error_diagnostics"] = "timeout: Qwen no completó la tarea en 5 minutos"
        state.setdefault("retry_count", 0)
        state["retry_count"] += 1
        return state
    
    stdout = proc.stdout
    state["last_execution_logs"] = stdout + "\n" + proc.stderr
    
    # Extraer resumen
    summary = "Diagnóstico completado."
    m = re.search(r"\"summary\":\s*\"(.*?)\"", stdout)
    if m: summary = m.group(1)
    
    # Registrar contexto del agente
    state["agent_context"] = state.get("agent_context", {})
    state["agent_context"]["qoder_diagnostics"] = {
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }
    
    return state


def node_pi_audit(state: TeamState) -> TeamState:
    print("[HERMES LOG] Ejecutando auditoría con Pi (qoder role)...")
    project_root = _project_path(state, ".")
    prompt = state.get("project_prompt") or "Audita el código y reporta vulnerabilidades."
    
    # Contexto de STATE.md
    state_path = project_root / ".harness" / "STATE.md"
    state_content = ""
    if state_path.exists():
        state_content = state_path.read_text(encoding="utf-8")

    full_prompt = (
        f"Eres un agente de auditoría (qoder). Revisa el código en busca de vulnerabilidades.\n"
        f"Contexto del proyecto (STATE.md):\n{state_content}\n\n"
        f"Instrucción específica: {prompt}"
    )

    cmd = [
        "pi",
        "--mode", "json",
        "--max-session-turns", "10",
        "--max-tool-calls", "40",
        "--max-wall-time", "10m",
        "-p", full_prompt,
    ]
    try:
        proc = subprocess.run(_resolve_cmd(cmd), cwd=str(project_root), capture_output=True, text=True, check=False, timeout=300, env=_with_extended_env())
    except subprocess.TimeoutExpired:
        state["last_execution_logs"] = "Qoder timeout (5 min)"
        state["error_diagnostics"] = "timeout: Qoder no completó la tarea en 5 minutos"
        state.setdefault("retry_count", 0)
        state["retry_count"] += 1
        return state
    
    stdout = proc.stdout
    state["last_execution_logs"] = stdout + "\n" + proc.stderr
    
    # Extraer resumen
    summary = "Auditoría completada."
    m = re.search(r"\"summary\":\s*\"(.*?)\"", stdout)
    if m: summary = m.group(1)
    
    # Registrar contexto del agente
    state["agent_context"] = state.get("agent_context", {})
    state["agent_context"]["pi_audit"] = {
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }
    
    return state