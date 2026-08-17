#!/usr/bin/env python3
"""
Code Guardian — Finalize Fix

Preenche .env.example/.env.local com placeholders e mostra o git status.
Commit só acontece com --commit explícito (AUDIT_SCOPE.md: nenhum commit
sem confirmação do usuário). Nunca faz push.

Execute:
  python finalize-fix.py <repo> [--commit]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main(repo_path: str, do_commit: bool):
    repo = Path(repo_path)
    
    if not repo.exists():
        print(f"❌ ERRO: Repo não encontrado em {repo}")
        return
    
    print("🛡️ Code Guardian — Finalizando Correcoes")
    print("="*70)
    print(f"\n📁 Repositô´´´rio: {repo}")
    print("="*70)
    
    # 1. Preencher .env.example
    print("\n\n📝 Preenchendo .env.example...")
    print("-"*70)
    
    env_example = repo / ".env.example"
    
    if not env_example.exists():
        env_example.write_text("# Variaveis de ambiente\n", encoding="utf-8")
    
    env_content = env_example.read_text(encoding="utf-8")
    
    # Adicionar variaveis se nao existirem
    env_vars = {
        "API_KEY": "test_api_key_placeholder",
        "SENHA": "test_senha_placeholder",
        "PASSWORD": "test_password_placeholder",
    }
    
    added = []
    for var, value in env_vars.items():
        if f"{var}=" not in env_content:
            env_content += f"{var}={value}\n"
            added.append(var)
    
    if added:
        env_example.write_text(env_content, encoding="utf-8")
        print(f"✅ Adicionado ao .env.example: {', '.join(added)}")
    else:
        print("✅ .env.example já está completo")
    
    # 2. Criar .env.local
    print("\n\n🔐 Criando .env.local...")
    print("-"*70)
    
    env_local = repo / ".env.local"
    
    if not env_local.exists():
        env_local.write_text("# Variaveis de ambiente (NAO COMMIT!)\n", encoding="utf-8")
        for var, value in env_vars.items():
            env_local.write_text(f"{var}={value}\n", encoding="utf-8")
        print("✅ .env.local criado")
        print("⚠️  Preencha com valores reais antes de rodar os testes!")
    else:
        print("✅ .env.local já existe")
    
    # 3. Git status (sempre mostrado, nunca staged automaticamente)
    print("\n\n📊 Git status:")
    print("-"*70)

    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )

    if result.stdout.strip():
        print(result.stdout)
    else:
        print("Nenhuma mudança pendente")

    # 4. Commit — só com --commit explícito (AUDIT_SCOPE.md: nada de commit
    # automático sem confirmação do usuário)
    if not do_commit:
        print("\n\n💾 Commit — PULADO (rode com --commit para revisar e commitar)")
        print("-"*70)
        print("Revise o `git status`/`git diff` acima antes de commitar manualmente.")
    else:
        print("\n\n💾 Commit...")
        print("-"*70)

        subprocess.run(["git", "add", "."], cwd=repo)

        result = subprocess.run(
            ["git", "commit", "-m", "fix: remove hardcoded credentials (security)"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        if result.returncode == 0:
            print(f"✅ Commit realizado:\n   {result.stdout.strip()}")
        else:
            if "nothing to commit" in result.stdout.lower() or "nothing to commit" in result.stderr.lower():
                print("⚠️  Nenhuma mudança para commit (já está limpo)")
            else:
                print(f"⚠️  Erro no commit: {result.stderr[:200]}")

    # 6. Resumo
    print("\n\n" + "="*70)
    print("✅ FINALIZACAO CONCLUÍ´`DA!")
    print("="*70)
    print("\n📝 Resumo:")
    print("   - .env.example preenchido")
    print("   - .env.local criado (não commit!)")
    print(f"   - Commit: {'realizado' if do_commit else 'PULADO (sem --commit)'}")
    print("\n⚠️  IMPORTANTE:")
    print("   1. Preencha .env.local com valores reais")
    print("   2. Teste os apps")
    print("   3. git push é sempre manual — este script nunca dá push")
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    parser.add_argument("--commit", action="store_true", help="Faz git add + commit ao final. Sem essa flag, só mostra o status.")
    args = parser.parse_args()

    main(args.repo_path, args.commit)
