#!/usr/bin/env python3
"""
Code Guardian — Integrate All

Por padrão só faz pull + testes e reporta o estado — nunca dá push sem
--push explícito, e falha de teste real interrompe o fluxo (não é mais
tratada como "continuando"). Ver AUDIT_SCOPE.md: nenhum push sem
confirmação explícita do usuário.
"""
import argparse
import subprocess
import sys
from pathlib import Path

def fill_env_local(repo_path: Path):
    print("\n🔐 Preenchendo .env.local...")
    print("-"*70)
    env_local = repo_path / ".env.local"
    if not env_local.exists():
        env_local.write_text("# Variaveis de ambiente (NAO COMMIT!)\n", encoding="utf-8")
    content = env_local.read_text(encoding="utf-8")
    env_vars = {"API_KEY": "sua_api_key_real_aqui", "SENHA": "sua_senha_real_aqui", "PASSWORD": "seu_password_real_aqui"}
    added = []
    for var, value in env_vars.items():
        if f"{var}=" not in content:
            content += f"{var}={value}\n"
            added.append(var)
    if added:
        env_local.write_text(content, encoding="utf-8")
        print(f"✅ Adicionado ao .env.local: {', '.join(added)}")
        print("⚠️  EDITE .env.local COM VALORES REAIS!")
    else:
        print("✅ .env.local já está completo")
    return True

def run_tests(repo_path: Path):
    print("\n🧪 Rodando testes...")
    print("-"*70)
    package_json = repo_path / "package.json"
    if not package_json.exists():
        print("⚠️  package.json não encontrado - pulando testes")
        return True
    import json
    pkg = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = pkg.get("scripts", {})
    if "test" not in scripts:
        print("⚠️  Script 'test' não encontrado no package.json - pulando (OK)")
        return True
    print("📦 Executando npm test...")
    result = subprocess.run(["npm", "test"], cwd=repo_path, capture_output=True, text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if result.returncode != 0:
        if "Missing script" in result.stderr or "npm ERR! missing script" in result.stderr:
            print("⚠️  Testes não configurados - pulando (OK)")
            return True
        print("❌ Testes falharam:")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        return False
    print(result.stdout)
    print("✅ Testes passaram!")
    return True

def git_pull(repo_path: Path):
    print("\n📥 Git pull...")
    print("-"*70)
    result = subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=repo_path, capture_output=True, text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        if "nothing to do" in result.stdout.lower() or "already up to date" in result.stdout.lower():
            print("✅ Já está atualizado com o remote")
            return True
        print("⚠️  Pull encontrou problemas")
        return False
    print("✅ Pull concluí·´do!")
    return True

def git_push(repo_path: Path):
    print("\n📤 Git push...")
    print("-"*70)
    result = subprocess.run(["git", "push", "origin", "main"], cwd=repo_path, capture_output=True, text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print("❌ ERRO no push")
        return False
    print("✅ Push concluí·´do!")
    return True

def main(repo_path: str, do_push: bool):
    repo = Path(repo_path)
    if not repo.exists():
        print(f"❌ ERRO: Repo não encontrado em {repo}")
        return
    print("🚀 Code Guardian — Integrate All")
    print(f"Modo: {'com push' if do_push else 'SEM push (default) — rode com --push para empurrar'}")
    print("="*70)
    print(f"\n📁 Repositô´´´rio: {repo}")
    print("="*70)

    steps = [("git_pull", lambda: git_pull(repo)), ("fill_env_local", lambda: fill_env_local(repo)), ("run_tests", lambda: run_tests(repo))]
    results = {}
    for step_name, step_func in steps:
        try:
            results[step_name] = step_func()
        except Exception as e:
            print(f"\n❌ ERRO em {step_name}: {e}")
            results[step_name] = False

    tests_ok = results.get("run_tests", False)
    if do_push:
        if tests_ok:
            results["git_push"] = git_push(repo)
        else:
            print("\n⚠️  Push cancelado: testes falharam. Corrija antes de empurrar.")
            results["git_push"] = False
    else:
        print("\nℹ️  --push não foi passado: nenhum commit/push será feito.")

    print("\n\n" + "="*70)
    print("📊 RESUMO DA INTEGRACAO")
    print("="*70)
    for step_name, passed in results.items():
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {step_name}: {'PASS' if passed else 'FAIL'}")
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed and do_push:
        print("✅ TODOS OS PASSOS CONCLUÍDOS, PUSH REALIZADO!")
    elif all_passed:
        print("✅ Pull e testes OK. Revise e rode com --push quando confirmar.")
    else:
        print("⚠️  ALGUNS PASSOS FALHARAM!")
    print("="*70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    parser.add_argument("--push", action="store_true", help="Faz git push origin main ao final, só se os testes passarem. Sem essa flag, nunca dá push.")
    args = parser.parse_args()
    main(args.repo_path, args.push)
