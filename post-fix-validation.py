#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path

def validate_no_hardcoded_creds(repo_path: Path):
    patterns = [
        (r'(?i)(password|passwd|pwd|senha)\s*=\s*["\'][^"\']+["\']', "Senha hardcoded"),
        (r'(?i)(api_key|apikey|api-key|secret_key)\s*=\s*["\'][^"\']+["\']', "API Key hardcoded"),
        (r'(?i)(token|auth_token|access_token)\s*=\s*["\'][^"\']+["\']', "Token hardcoded"),
    ]
    issues = []
    for ext in ["*.ts", "*.js", "*.py", "*.json"]:
        for file_path in repo_path.rglob(ext):
            if any(d in str(file_path) for d in ["node_modules", ".git", "venv", "dist", "build", "diagnostico"]):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except:
                continue
            for pattern, description in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    if "process.env" in match.group(0) or "os.environ" in match.group(0):
                        continue
                    if "placeholder" in match.group(0).lower() or "test_" in match.group(0).lower():
                        continue
                    issues.append({"file": str(file_path.relative_to(repo_path)), "type": description, "code": match.group(0)[:80]})
    if issues:
        print(f"❌ {len(issues)} hardcoded credential(s) encontrada(s):")
        for issue in issues[:10]:
            print(f"   🔴 {issue['file']}: {issue['type']}")
            print(f"      {issue['code']}")
        return False
    else:
        print("✅ Nenhuma hardcoded credential encontrada!")
        return True

def validate_syntax_nodejs(repo_path: Path):
    issues = []
    for ext in ["*.ts", "*.js"]:
        for file_path in repo_path.rglob(ext):
            if any(d in str(file_path) for d in ["node_modules", ".git", "venv", "dist", "build", "diagnostico"]):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except:
                continue
            if re.search(r'process\.env\.get\(', content):
                issues.append(str(file_path.relative_to(repo_path)))
    if issues:
        print(f"❌ {len(issues)} arquivo(s) com syntax Python em Node.js:")
        for issue in issues[:10]:
            print(f"   🔴 {issue}")
        return False
    else:
        print("✅ Syntax Node.js correta em todos os arquivos!")
        return True

def validate_env_files(repo_path: Path):
    env_example = repo_path / ".env.example"
    if env_example.exists():
        print("✅ .env.example existe")
        content = env_example.read_text(encoding="utf-8")
        vars_count = len([l for l in content.split("\n") if "=" in l and not l.startswith("#")])
        print(f"   📝 {vars_count} variavel(eis) definida(s)")
    else:
        print("⚠️  .env.example não encontrado")
    env_local = repo_path / ".env.local"
    if env_local.exists():
        print("✅ .env.local existe")
    else:
        print("⚠️  .env.local não encontrado (crie para desenvolvimento local)")
    gitignore = repo_path / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".env" in content:
            print("✅ .env está no .gitignore")
        else:
            print("⚠️  .env NÃO está no .gitignore (adicione!)")
    return True

def validate_git_status(repo_path: Path):
    result = subprocess.run(["git", "status", "--short"], cwd=repo_path, capture_output=True, text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)
    if result.stdout.strip():
        lines = result.stdout.strip().split("\n")
        print(f"📊 {len(lines)} arquivo(s) modificados/novos:")
        for line in lines[:10]:
            print(f"   {line}")
        if len(lines) > 10:
            print(f"   ... e mais {len(lines) - 10}")
    else:
        print("✅ Working tree limpo")
    result = subprocess.run(["git", "rev-list", "--left-right", "--count", "HEAD...origin/HEAD"], cwd=repo_path, capture_output=True, text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)
    if result.stdout.strip():
        parts = result.stdout.strip().split()
        if len(parts) == 2:
            behind, ahead = parts
            if behind != "0":
                print(f"⚠️  Atrasado: {behind} commits atrás do remote")
                print(f"   Execute: git pull origin")
            if ahead != "0":
                print(f"⚠️  Adiantado: {ahead} commits à frente do remote")
                print(f"   Execute: git push origin")
            if behind == "0" and ahead == "0":
                print("✅ Sincronizado com remote")
    return True

def validate_quick_security(repo_path: Path):
    issues = []
    for ext in ["*.ts", "*.js"]:
        for file_path in repo_path.rglob(ext):
            if any(d in str(file_path) for d in ["node_modules", ".git", "venv", "dist", "build", "diagnostico"]):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except:
                continue
            if re.search(r'\beval\s*\(', content):
                issues.append(f"eval() em {file_path.relative_to(repo_path)}")
    for file_path in repo_path.rglob("*.ts"):
        if "prod" in str(file_path) or "release" in str(file_path):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except:
                continue
            if "console.log" in content:
                issues.append(f"console.log em {file_path.relative_to(repo_path)}")
    if issues:
        print(f"⚠️  {len(issues)} alerta(s) de seguranca:")
        for issue in issues[:10]:
            print(f"   🟡 {issue}")
    else:
        print("✅ Nenhum alerta de seguranca encontrado!")
    return len(issues) == 0

def main(repo_path: str):
    repo = Path(repo_path)
    if not repo.exists():
        print(f"❌ ERRO: Repo não encontrado em {repo}")
        return
    print("🛡️ Code Guardian — Post-Fix Validation")
    print("="*70)
    print(f"\n📁 Repositô´´´rio: {repo}")
    print("="*70)
    results = {}
    results["hardcoded_creds"] = validate_no_hardcoded_creds(repo)
    results["syntax_nodejs"] = validate_syntax_nodejs(repo)
    results["env_files"] = validate_env_files(repo)
    results["git_status"] = validate_git_status(repo)
    results["quick_security"] = validate_quick_security(repo)
    print("\n\n" + "="*70)
    print("📊 RESUMO DA VALIDACAO")
    print("="*70)
    for check, passed in results.items():
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {check}: {'PASS' if passed else 'FAIL'}")
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("✅ TODAS AS VALIDACOES PASSARAM!")
        print("\n🚀 Proximo passo: git push origin main")
    else:
        print("⚠️  ALGUMAS VALIDACOES FALHARAM!")
        print("\n📝 Revise os erros acima e corrija antes de fazer push.")
    print("="*70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python post-fix-validation.py <caminho-do-repo>")
        sys.exit(1)
    main(sys.argv[1])
