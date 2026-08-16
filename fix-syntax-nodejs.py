#!/usr/bin/env python3
"""
Code Guardian — Fix: Syntax Node.js

Corrige process.env.get() para process.env.VAR || ""

Execute:
  python fix-syntax-nodejs.py C:\AMILCAR-CONSTELATTION\estrelas\sbrgestao
"""

import re
import sys
from pathlib import Path


def fix_file(file_path: Path, repo_path: Path):
    """Corrige syntax de Python para Node.js"""
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠️ Erro ao ler {file_path.name}: {e}")
        return False
    
    original_content = content
    
    # Pattern: process.env.get("VAR", "") → process.env.VAR || ""
    pattern = r'process\.env\.get\("([A-Z_]+)",\s*""\)'
    
    fixes = []
    for match in re.finditer(pattern, content):
        var_name = match.group(1)
        old_code = match.group(0)
        new_code = f'process.env.{var_name} || ""'
        
        content = content.replace(old_code, new_code)
        fixes.append(f'{var_name}: {old_code} → {new_code}')
    
    # Se houve mudanças, salva
    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        
        print(f"\n✅ {file_path.relative_to(repo_path)}")
        for fix in fixes:
            print(f"   - {fix}")
        
        return True
    else:
        return False


def main(repo_path: str):
    """Corrige todos os arquivos .ts e .js"""
    
    repo = Path(repo_path)
    
    if not repo.exists():
        print(f"❌ ERRO: Repo não encontrado em {repo}")
        return
    
    print("🛡️ Code Guardian — Fix: Syntax Node.js")
    print("="*70)
    print(f"\n📁 Repositô´´´rio: {repo}")
    print("="*70)
    
    # Arquivos para corrigir
    files_to_fix = [
        repo / "apps/agnvendas/apps/api/src/test/env-setup.ts",
        repo / "apps/agnvendas/apps/api/src/test/factories.ts",
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
    print("="*70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python fix-syntax-nodejs.py <caminho-do-repo>")
        print("\nExemplo:")
        print("  python fix-syntax-nodejs.py C:\\AMILCAR-CONSTELATTION\\estrelas\\sbrgestao")
        sys.exit(1)
    
    main(sys.argv[1])
