#!/usr/bin/env python3
"""
Code Guardian — Fix: Hardcoded Credentials

Remove hardcoded credentials e move para .env

Execute:
  python fix-hardcoded-creds.py C:\AMILCAR-CONSTELATTION\estrelas\sbrgestao
"""

import re
import sys
from pathlib import Path


def fix_file(file_path: Path, repo_path: Path):
    """Corrige um arquivo removendo hardcoded credentials"""
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠️ Erro ao ler {file_path.name}: {e}")
        return False
    
    original_content = content
    fixes = []
    
    # Pattern para senhas
    password_pattern = r'(?i)(password|passwd|pwd|senha)\s*=\s*["\']([^"\']+)["\']'
    
    # Pattern para API keys
    api_key_pattern = r'(?i)(api_key|apikey|api-key|secret_key)\s*=\s*["\']([^"\']+)["\']'
    
    # Pattern para tokens
    token_pattern = r'(?i)(token|auth_token|access_token)\s*=\s*["\']([^"\']+)["\']'
    
    # Substituir senhas
    for match in re.finditer(password_pattern, content):
        var_name = match.group(1).lower().replace('-', '_')
        content = content.replace(
            match.group(0),
            f'{match.group(1)} = process.env.get("{var_name.upper()}", "")'
        )
        fixes.append(f"Senha → process.env.{var_name.upper()}")
    
    # Substituir API keys
    for match in re.finditer(api_key_pattern, content):
        var_name = match.group(1).lower().replace('-', '_')
        content = content.replace(
            match.group(0),
            f'{match.group(1)} = process.env.get("{var_name.upper()}", "")'
        )
        fixes.append(f"API Key → process.env.{var_name.upper()}")
    
    # Substituir tokens
    for match in re.finditer(token_pattern, content):
        var_name = match.group(1).lower().replace('-', '_')
        content = content.replace(
            match.group(0),
            f'{match.group(1)} = process.env.get("{var_name.upper()}", "")'
        )
        fixes.append(f"Token → process.env.{var_name.upper()}")
    
    # Se houve mudanças, salva o arquivo
    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        
        print(f"\n✅ {file_path.relative_to(repo_path)}")
        for fix in fixes:
            print(f"   - {fix}")
        
        # Adicionar ao .env.example
        env_example = repo_path / ".env.example"
        env_vars_added = []
        
        if not env_example.exists():
            env_example.write_text("# Variaveis de ambiente\n", encoding="utf-8")
        
        env_content = env_example.read_text(encoding="utf-8")
        
        for match in re.finditer(password_pattern, original_content):
            var_name = match.group(1).upper()
            if var_name not in env_content:
                env_vars_added.append(f"{var_name}=")
        
        for match in re.finditer(api_key_pattern, original_content):
            var_name = match.group(1).upper()
            if var_name not in env_content:
                env_vars_added.append(f"{var_name}=")
        
        for match in re.finditer(token_pattern, original_content):
            var_name = match.group(1).upper()
            if var_name not in env_content:
                env_vars_added.append(f"{var_name}=")
        
        if env_vars_added:
            env_content += "\n# Adicionado por code-guardian\n"
            env_content += "\n".join(env_vars_added) + "\n"
            env_example.write_text(env_content, encoding="utf-8")
            print(f"   📝 Adicionado ao .env.example: {', '.join(env_vars_added)}")
        
        return True
    else:
        print(f"⚠️ {file_path.relative_to(repo_path)} - Nenhuma mudança necessária")
        return False


def main(repo_path: str):
    """Corrige todos os arquivos com hardcoded credentials"""
    
    repo = Path(repo_path)
    
    if not repo.exists():
        print(f"❌ ERRO: Repo não encontrado em {repo}")
        return
    
    print("🛡️ Code Guardian — Fix: Hardcoded Credentials")
    print("="*70)
    print(f"\n📁 Repositô´´´rio: {repo}")
    print("="*70)
    
    # Arquivos com issues (do diagnostico)
    files_to_fix = [
        repo / "apps/agnvendas/apps/api/src/test/env-setup.ts",
        repo / "apps/agnvendas/apps/api/src/test/factories.ts",
        repo / "apps/ponto-ti/rep_client.py",
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if file_path.exists():
            if fix_file(file_path, repo):
                fixed_count += 1
        else:
            print(f"⚠️ Arquivo não encontrado: {file_path}")
    
    print("\n" + "="*70)
    print(f"✅ Correçªµes concluí´´das!")
    print(f"   {fixed_count} arquivo(s) corrigido(s)")
    print("\n⚠️  IMPORTANTE:")
    print("   1. Revise as mudanças")
    print("   2. Preencha .env.example com os valores reais")
    print("   3. Nunca commit .env real!")
    print("="*70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python fix-hardcoded-creds.py <caminho-do-repo>")
        print("\nExemplo:")
        print("  python fix-hardcoded-creds.py C:\\AMILCAR-CONSTELATTION\\estrelas\\sbrgestao")
        sys.exit(1)
    
    main(sys.argv[1])
