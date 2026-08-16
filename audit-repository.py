#!/usr/bin/env python3
"""
audit-repository.py

Orquestrador de auditoria de repositório em modo leitura para o Code Guardian Toolkit.

Uso:
  python audit-repository.py <caminho_do_repositorio> --report-dir <caminho_do_relatorio>

Exemplo:
  python audit-repository.py r"D:\PROJETOS\THEUNIVERSE\theuniverse\corpos\kuiper\araujo-informatica\hospital360-v2-remote" --report-dir r"D:\AUDITORIAS\hospital360-v2"

Comportamento:
- Não faz fetch, pull, commit, push, issue ou PR.
- Não cria, sobrescreve ou lê .env.
- Não inicia Docker, banco, aplicação ou navegador.
- Não executa scripts do repositório auditado.
- Gera relatórios JSON e Markdown fora do repositório auditado.
- Nunca persiste o valor potencialmente secreto no relatório.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MAX_FILE_SIZE_BYTES = 1_000_000
TEXT_EXTENSIONS = {
    ".php", ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".env", ".env.*", ".md", ".txt", ".rst", ".sh", ".bat", ".ps1",
    ".sql", ".graphql", ".gql", ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".xml", ".proto", ".properties", ".gitignore", ".editorconfig", ".dockerfile",
    ".tf", ".hcl", ".rb", ".java", ".go", ".rs", ".swift", ".kt", ".kts",
    ".cs", ".fs", ".fsx", ".vue", ".svelte", ".astro", ".prisma", ".lock",
}
IGNORED_FILES = {
    ".DS_Store", "Thumbs.db", "*.lock", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "composer.lock", "poetry.lock", "Cargo.lock",
}

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"gho_[A-Za-z0-9]{36}"),
    re.compile(r"ghu_[A-Za-z0-9]{36}"),
    re.compile(r"ghs_[A-Za-z0-9]{36}"),
    re.compile(r"ghr_[A-Za-z0-9]{36}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|pwd|senha)\s*[:=]\s*['\"][^'\"]{4,}['\"]"),
    re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"(?i)(token|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"(?i)(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@"),
]

PLACEHOLDER_PATTERNS = [
    re.compile(r"(?i)\b(your[_-]?(api[_-]?key|token|secret|password|senha))\b"),
    re.compile(r"(?i)\b(example|fake|dummy|mock|placeholder)[_-]?(key|token|secret|password|senha)\b"),
    re.compile(r"(?i)\b(seu[_-]?(token|senha|apikey|api[_-]?key))\b"),
    re.compile(r"(?i)\b(ghp_|gho_|ghu_|ghs_|ghr_|AKIA)[X0]+\b"),
    re.compile(r"-----BEGIN .* PRIVATE KEY-----[\s\S]*?-----END .* PRIVATE KEY-----"),
]


def run_git_command(repo_path: Path, args: List[str]) -> Tuple[Optional[str], Optional[str]]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip(), result.stderr.strip()
    except Exception as exc:
        return None, str(exc)


def is_git_repo(path: Path) -> bool:
    return (path / ".git").is_dir()


def get_git_snapshot(repo_path: Path) -> Dict[str, Any]:
    branch, _ = run_git_command(repo_path, ["branch", "--show-current"])
    head, _ = run_git_command(repo_path, ["rev-parse", "HEAD"])
    origin_url, _ = run_git_command(repo_path, ["remote", "get-url", "origin"])
    status, _ = run_git_command(repo_path, ["status", "--short"])
    snapshot: Dict[str, Any] = {
        "branch": branch or "(detached)",
        "head": head,
        "origin": origin_url,
        "status_short": status or "",
        "divergence": None,
    }
    if branch and origin_url:
        output, _ = run_git_command(
            repo_path,
            ["rev-list", "--left-right", "--count", f"HEAD...origin/{branch}"],
        )
        if output:
            try:
                ahead, behind = map(int, output.split())
                snapshot["divergence"] = {"ahead": ahead, "behind": behind}
            except ValueError:
                snapshot["divergence"] = {"ahead": None, "behind": None}
    return snapshot


def detect_stack(repo_path: Path) -> Dict[str, Any]:
    manifests = {
        "package.json": "node",
        "composer.json": "php_composer",
        "requirements.txt": "python_pip",
        "pyproject.toml": "python_pyproject",
        "Gemfile": "ruby_bundler",
        "go.mod": "go_modules",
        "Cargo.toml": "rust_cargo",
        "pom.xml": "java_maven",
        "build.gradle": "java_gradle",
    }
    return {
        "manifests": [label for filename, label in manifests.items() if (repo_path / filename).exists()],
        "docker": (repo_path / "docker-compose.yml").exists() or (repo_path / "Dockerfile").exists(),
        "playwright": (repo_path / "playwright.config.ts").exists() or (repo_path / "playwright.config.js").exists(),
    }


def load_gitignore(repo_path: Path) -> List[str]:
    gitignore_path = repo_path / ".gitignore"
    if not gitignore_path.is_file():
        return []
    try:
        with gitignore_path.open("r", encoding="utf-8", errors="ignore") as handle:
            return [line.strip() for line in handle if line.strip() and not line.startswith("#")]
    except OSError:
        return []


def is_ignored_by_gitignore(rel_path: str, rules: List[str]) -> bool:
    import fnmatch

    normalized = rel_path.replace("\\", "/")
    ignored = False
    for rule in rules:
        negated = rule.startswith("!")
        pattern = rule[1:] if negated else rule
        if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(Path(normalized).name, pattern.rstrip("/")):
            ignored = not negated
    return ignored


def list_tracked_files(repo_path: Path) -> List[str]:
    output, _ = run_git_command(repo_path, ["ls-files", "-z"])
    return [item for item in (output or "").split("\0") if item]


def is_text_file(path: Path) -> bool:
    return path.name in {".gitignore", ".editorconfig", "Dockerfile"} or path.suffix.lower() in TEXT_EXTENSIONS


def is_ignored_file(name: str) -> bool:
    import fnmatch
    return any(fnmatch.fnmatch(name, pattern) for pattern in IGNORED_FILES)


def classify_secret(line: str) -> str:
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(line):
            return "placeholder"
    for pattern in SECRET_PATTERNS:
        if pattern.search(line):
            return "suspect"
    return "clean"


def redact_evidence(line: str) -> str:
    label_match = re.search(r"(?i)\b(password|passwd|pwd|senha|api[_-]?key|apikey|token|secret)\b", line)
    if label_match:
        return f"{label_match.group(1)} = [REDACTED]"
    if "PRIVATE KEY" in line:
        return "[PRIVATE KEY MATERIAL REDACTED]"
    if re.search(r"(?i)(postgres|mysql|mongodb|redis)://", line):
        return "[DATABASE URL WITH CREDENTIALS REDACTED]"
    return "[POTENTIAL SECRET REDACTED]"


def scan_file_for_secrets(file_path: Path, rel_path: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return findings
        with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line_no, line in enumerate(handle, start=1):
                classification = classify_secret(line)
                if classification != "clean":
                    findings.append({
                        "file": rel_path,
                        "line": line_no,
                        "classification": classification,
                        "evidence": redact_evidence(line),
                    })
    except OSError:
        pass
    return findings


def check_sensitive_paths_tracked(tracked: List[str]) -> List[Dict[str, str]]:
    sensitive_patterns = [
        r"(^|/)\.env($|\.)", r"\.pem$", r"\.key$", r"\.p12$", r"\.pfx$",
        r"(^|/)id_rsa$", r"(^|/)id_ed25519$", r"(^|/)\.ssh/",
    ]
    issues = []
    for rel_path in tracked:
        if any(re.search(pattern, rel_path, re.IGNORECASE) for pattern in sensitive_patterns):
            if Path(rel_path).name not in {".env.example", ".env.sample", ".env.template"}:
                issues.append({"path": rel_path, "reason": "tracked_sensitive_path"})
    return issues


def check_gitignore_coverage(gitignore_rules: List[str]) -> List[Dict[str, str]]:
    issues = []
    for path in [".env", ".env.local", ".env.test"]:
        if not is_ignored_by_gitignore(path, gitignore_rules):
            issues.append({"path": path, "reason": "not_ignored_by_gitignore"})
    return issues


def discover_package_scripts(repo_path: Path) -> Optional[Dict[str, str]]:
    package_json = repo_path / "package.json"
    if not package_json.is_file():
        return None
    try:
        with package_json.open("r", encoding="utf-8") as handle:
            scripts = json.load(handle).get("scripts", {})
        return scripts if isinstance(scripts, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def build_markdown_report(report: Dict[str, Any]) -> str:
    git = report["git"]
    summary = report["summary"]
    lines = [
        "# Relatório de Auditoria de Repositório",
        "",
        f"**Repositório:** `{report['repo_path']}`",
        f"**Data:** `{report['timestamp']}`",
        "",
        "## Estado Git",
        "",
        f"- Branch: `{git.get('branch', 'N/A')}`",
        f"- HEAD: `{(git.get('head') or 'N/A')[:12]}`",
        f"- Origin: `{git.get('origin') or 'N/A'}`",
        f"- Alterações locais: {'sim' if git.get('status_short') else 'não'}",
        "",
        "## Stack Detectada",
        "",
        f"- Manifestos: {', '.join(report['stack']['manifests']) or 'nenhum'}",
        f"- Docker: {'sim' if report['stack']['docker'] else 'não'}",
        f"- Playwright: {'sim' if report['stack']['playwright'] else 'não'}",
        "",
        "## .gitignore",
        "",
        f"- Regras encontradas: {report['gitignore']['rules_count']}",
    ]
    not_ignored = report["gitignore"]["sensitive_not_ignored"]
    if not_ignored:
        lines.extend(f"- Atenção: `{item['path']}` ({item['reason']})" for item in not_ignored)
    else:
        lines.append("- Cobertura esperada para arquivos `.env`: OK")
    lines.extend(["", "## Caminhos Sensíveis Rastreados", ""])
    tracked = report["sensitive_tracked"]
    if tracked:
        lines.extend(f"- `{item['path']}` ({item['reason']})" for item in tracked)
    else:
        lines.append("- Nenhum caminho sensível rastreado detectado.")
    lines.extend(["", "## Scripts Descobertos", ""])
    scripts = report.get("scripts_discovered")
    if scripts:
        lines.extend(f"- `{name}`: `{command}`" for name, command in scripts.items())
    else:
        lines.append("- Nenhum script descoberto ou package.json ausente.")
    lines.extend([
        "",
        "## Achados de Segredo",
        "",
        f"- Arquivos escaneados: {summary['files_scanned']}",
        f"- Total de achados: {summary['findings_total']}",
        f"- Suspeitos: {summary['findings_suspect']}",
        f"- Placeholders: {summary['findings_placeholder']}",
        "",
    ])
    findings = report["secrets_findings"]
    if findings:
        lines.extend([
            "| Arquivo | Linha | Classificação | Evidência |",
            "|---|---:|---|---|",
        ])
        lines.extend(
            f"| `{item['file']}` | {item['line']} | {item['classification']} | {item['evidence']} |"
            for item in findings
        )
    else:
        lines.append("- Nenhum achado de segredo detectado nos arquivos escaneados.")
    lines.extend([
        "",
        "## Limitações",
        "",
        "- Auditoria em modo leitura: não houve fetch, pull, commit, push, issue ou PR.",
        "- Não foram lidos arquivos ignorados pelo `.gitignore`.",
        "- Arquivos binários e arquivos maiores que 1 MB foram ignorados.",
        "- Nenhum achado não é garantia absoluta de ausência de segredos.",
        "",
        "## Status",
        "",
        f"- Código de saída: `{summary['status_code']}`",
        "- 0: nenhum achado suspeito/alto risco.",
        "- 1: achados suspeitos ou alto risco.",
        "- 2: execução bloqueada ou erro de configuração.",
        "",
    ])
    return "\n".join(lines)


def build_report(repo_path: Path) -> Dict[str, Any]:
    rules = load_gitignore(repo_path)
    tracked = list_tracked_files(repo_path)
    findings: List[Dict[str, Any]] = []
    files_scanned = 0
    for relative_path in tracked:
        path = Path(relative_path)
        if is_ignored_file(path.name) or not is_text_file(path):
            continue
        if is_ignored_by_gitignore(relative_path, rules):
            continue
        full_path = repo_path / relative_path
        if not full_path.is_file():
            continue
        files_scanned += 1
        findings.extend(scan_file_for_secrets(full_path, relative_path.replace("\\", "/")))

    suspect_count = sum(item["classification"] == "suspect" for item in findings)
    sensitive_tracked = check_sensitive_paths_tracked(tracked)
    status_code = 2 if sensitive_tracked else 1 if suspect_count else 0
    return {
        "repo_path": str(repo_path),
        "timestamp": datetime.now().isoformat(),
        "git": get_git_snapshot(repo_path),
        "stack": detect_stack(repo_path),
        "gitignore": {
            "rules_count": len(rules),
            "sensitive_not_ignored": check_gitignore_coverage(rules),
        },
        "sensitive_tracked": sensitive_tracked,
        "secrets_findings": findings,
        "scripts_discovered": discover_package_scripts(repo_path),
        "summary": {
            "files_scanned": files_scanned,
            "findings_total": len(findings),
            "findings_suspect": suspect_count,
            "findings_placeholder": sum(item["classification"] == "placeholder" for item in findings),
            "status_code": status_code,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoria de repositório em modo leitura.")
    parser.add_argument("repo_path", help="Caminho absoluto do repositório Git a auditar")
    parser.add_argument("--report-dir", required=True, help="Diretório externo para os relatórios")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    report_dir = Path(args.report_dir).resolve()
    if not repo_path.is_dir() or not is_git_repo(repo_path):
        print(f"Erro: diretório não é um repositório Git: {repo_path}", file=sys.stderr)
        return 2
    if not report_dir.is_dir():
        print(f"Erro: diretório de relatório não existe: {report_dir}", file=sys.stderr)
        return 2
    try:
        report_dir.relative_to(repo_path)
        print("Erro: o diretório de relatório não pode estar dentro do repositório auditado.", file=sys.stderr)
        return 2
    except ValueError:
        pass

    report = build_report(repo_path)
    base_name = f"audit-{datetime.now().strftime('%Y%m%d_%H%M%S')}-{repo_path.name}"
    json_path = report_dir / f"{base_name}.json"
    markdown_path = report_dir / f"{base_name}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text(build_markdown_report(report), encoding="utf-8")
    print(f"Relatório JSON: {json_path}")
    print(f"Relatório MD:   {markdown_path}")
    print(f"Status: {report['summary']['status_code']}")
    return report["summary"]["status_code"]


if __name__ == "__main__":
    sys.exit(main())
