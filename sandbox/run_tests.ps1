# run_tests.ps1 - Automated Test Execution for Hermes A2A Factory (Opción 1: Entorno uv)

$ErrorActionPreference = "Stop"
$hermesDir = "C:\Users\Agent\dev\hermes-factory"
$sandboxDir = "$hermesDir\sandbox"
$testProjectDir = "$sandboxDir\test-project"
$stubsDir = "$sandboxDir\stubs"

# Usar el path de Python de uv
$pythonExe = "C:\Users\Agent\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe"

Write-Host "--- 1. Preparar entorno ---"
cd $hermesDir
& $pythonExe -m pip install --break-system-packages -r requirements.txt

Write-Host "--- 2. Configurar archivos de prueba ---"
& $pythonExe "$sandboxDir\prepare_test_configs.py"

# Limpiar archivos de estado previos en test-project
if (Test-Path "$testProjectDir\.harness\STATE.md") { Remove-Item "$testProjectDir\.harness\STATE.md" }
if (Test-Path "$testProjectDir\.harness\BLOCKERS.md") { Remove-Item "$testProjectDir\.harness\BLOCKERS.md" }
if (Test-Path "$testProjectDir\.harness\STAGES.md") { Remove-Item "$testProjectDir\.harness\STAGES.md" }

# Crear un STAGES.md inicial para test-project
if (-not (Test-Path "$testProjectDir\.harness")) { New-Item -ItemType Directory -Path "$testProjectDir\.harness" }
@"
# STAGES
- [ ] Etapa 1: Scaffolding y Estructura Base
"@ | Out-File -FilePath "$testProjectDir\.harness\STAGES.md" -Encoding utf8

Write-Host "--- 3. Crear stubs CLI ---"
if (-not (Test-Path $stubsDir)) { New-Item -ItemType Directory -Path $stubsDir }

@"
import sys
import json
from pathlib import Path

args = sys.argv[1:]
sandbox_dir = Path(__file__).parent.parent
stages_path = sandbox_dir / "test-project" / ".harness" / "STAGES.md"

result = {
    "summary": "Scaffolding simulado exitoso por Qwen.",
    "status": "ok",
    "args": args
}

if stages_path.exists():
    current_content = stages_path.read_text(encoding="utf-8")
    if "Sub-paso activo:" not in current_content:
        lines = current_content.split("\n")
        lines.insert(1, "Sub-paso activo: 1.0")
        stages_path.write_text("\n".join(lines), encoding="utf-8")
        result["summary"] = "STAGES.md actualizado con Sub-paso activo: 1.0"

print(json.dumps(result))
sys.exit(0)
"@ | Out-File -FilePath "$stubsDir\qwen_stub.py" -Encoding utf8

@"
import sys
import json
from pathlib import Path

args = sys.argv[1:]
sandbox_dir = Path(__file__).parent.parent
stages_path = sandbox_dir / "test-project" / ".harness" / "STAGES.md"

result = {
    "summary": "Diseño simulado exitoso.",
    "status": "ok",
    "args": args
}

if stages_path.exists():
    current_content = stages_path.read_text(encoding="utf-8")
    if "Sub-paso activo:" not in current_content:
        lines = current_content.split("\n")
        lines.insert(1, "Sub-paso activo: 1.1")
        stages_path.write_text("\n".join(lines), encoding="utf-8")
        result["summary"] = "STAGES.md actualizado con Sub-paso activo: 1.1"

print(json.dumps(result))
sys.exit(0)
"@ | Out-File -FilePath "$stubsDir\vibe_stub.py" -Encoding utf8

@"
import sys
import json
from pathlib import Path

args = sys.argv[1:]
sandbox_dir = Path(__file__).parent.parent
stages_path = sandbox_dir / "test-project" / ".harness" / "STAGES.md"

result = {
    "summary": "Diagnóstico simulado exitoso.",
    "status": "ok",
    "args": args
}

if stages_path.exists():
    current_content = stages_path.read_text(encoding="utf-8")
    if "Sub-paso activo:" not in current_content:
        lines = current_content.split("\n")
        lines.insert(1, "Sub-paso activo: 1.2")
        stages_path.write_text("\n".join(lines), encoding="utf-8")
        result["summary"] = "STAGES.md actualizado con Sub-paso activo: 1.2"

print(json.dumps(result))
sys.exit(0)
"@ | Out-File -FilePath "$stubsDir\pi_stub.py" -Encoding utf8

@"
import sys
import json
from pathlib import Path

args = sys.argv[1:]
sandbox_dir = Path(__file__).parent.parent
stages_path = sandbox_dir / "test-project" / ".harness" / "STAGES.md"

result = {
    "summary": "Auditoría simulada exitosa.",
    "status": "ok",
    "args": args
}

if stages_path.exists():
    current_content = stages_path.read_text(encoding="utf-8")
    if "Sub-paso activo:" not in current_content:
        lines = current_content.split("\n")
        lines.insert(1, "Sub-paso activo: 2.0")
        stages_path.write_text("\n".join(lines), encoding="utf-8")
        result["summary"] = "STAGES.md actualizado con Sub-paso activo: 2.0"

print(json.dumps(result))
sys.exit(0)
"@ | Out-File -FilePath "$stubsDir\qwen_stub.py" -Encoding utf8

Write-Host "--- 4. Configurar .env ---"
# Respaldar .env actual si existe
if (Test-Path "$hermesDir\.env") { Copy-Item "$hermesDir\.env" "$hermesDir\.env.bak" -Force }

# Usar el path de Python de uv para los stubs
@"
CLI_PI=$pythonExe $stubsDir\pi_stub.py
CLI_VIBE=$pythonExe $stubsDir\vibe_stub.py
CLI_QWEN=$pythonExe $stubsDir\qwen_stub.py
CLI_QODERCLI=$pythonExe $stubsDir\qodercli_stub.py
"@ | Out-File -FilePath "$hermesDir\.env" -Encoding utf8

Write-Host "--- 5. Ejecutar el motor con el entorno de uv ---"
cd $hermesDir
# Asegurar que el entorno de uv esté en el PATH
$env:PATH = "C:\Users\Agent\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\Scripts;$env:PATH"
& $pythonExe workflow.py

Write-Host "--- 6. Validar resultados ---"
$stateFile = "$testProjectDir\.harness\STATE.md"
if (-not (Test-Path $stateFile)) {
    Write-Error "STATE.md no fue generado en $stateFile"
    exit 1
}

$stateContent = Get-Content $stateFile -Raw
Write-Host "Contenido de STATE.md:"
Write-Host $stateContent

$success = $true

if ($stateContent -match "quality_gate_passed: True") {
    Write-Host "[OK] quality_gate_passed: True"
} else {
    Write-Host "[FAIL] quality_gate_passed no es True" -ForegroundColor Red
    $success = $false
}

if ($stateContent -match "🟢 Salud: Verde") {
    Write-Host "[OK] Salud: Verde"
} else {
    Write-Host "[FAIL] Salud no es Verde o tiene doble prefijo" -ForegroundColor Red
    $success = $false
}

# Restaurar .env original
if (Test-Path "$hermesDir\.env.bak") { 
    Move-Item "$hermesDir\.env.bak" "$hermesDir\.env" -Force 
}

if ($success) {
    Write-Host "--- Pruebas completadas con ÉXITO ---"
} else {
    Write-Host "--- Pruebas completadas con ERRORES ---" -ForegroundColor Red
    exit 1
}
