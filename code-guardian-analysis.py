#!/usr/bin/env python3
"""
Code Guardian — Analysis

Analisa repo em busca de hardcoded credentials e outros problemas

Execute:
  python code-guardian-analysis.py <caminho-do-repo>
"""

import re
import sys
from pathlib import Path

def main(repo_path: str):
    repo = Path(repo_path)
    
    if not repo.exists():
        print(f"❌ ERRO: Repo não encontrado em {repo}")
        return
    
    print("🛡️ Code Guardian — Analise de Seguranca")
    print("="*70)
    print(f"\n📁 Repositô´´´rio: {repo}")
    print("="*70)
    
    patterns = [
        (r'(?i)(password|passwd|pwd|senha)\s*=\s*["\'][^"\']+["\']', "Senha hardcoded"),
        (r'(?i)(api_key|apikey|api-key|secret_key)\s*=\s*["\'][^"\']+["\']', "API Key hardcoded"),
        (r'(?i)(token|auth_token|access_token)\s*=\s*["\'][^"\']+["\']', "Token hardcoded"),
    ]
    
    issues = []
    files_scanned = 0
    
    for ext in ["*.ts", "*.js", "*.py", "*.json", "*.env", "*.yml", "*.yaml"]:
        for file_path in repo.rglob(ext):
            if any(d in str(file_path) for d in ["node_modules", ".git", "venv", "dist", "build", "diagnostico"]):
                continue
            
            files_scanned += 1
            
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
                    
                    issues.append({
                        "file": str(file_path.relative_to(repo)),
                        "type": description,
                        "code": match.group(0)[:80]
                    })
    
    print(f"\n📊 Arquivos escaneados: {files_scanned}")
    print(f"📊 Problemas encontrados: {len(issues)}")
    print("="*70)
    
    if issues:
        print("\n🔴 Problemas:\n")
        for issue in issues[:20]:
            print(f"   {issue['file']}")
            print(f"      {issue['type']}: {issue['code']}\n")
        
        if len(issues) > 20:
            print(f"   ... e mais {len(issues) - 20} problemas")
        
        print("\n" + "="*70)
        print("⚠️  HARDCODED CREDENTIALS DETECTADAS!")
        print("\n📝 Proximos passos:")
        print("   1. Rode fix-hardcoded-creds.py para corrigir")
        print("   2. Rode finalize-fix.py para commit")
        print("   3. Rode post-fix-validation.py para validar")
        print("   4. Rode integrate-all.py para integrar tudo")
        print("="*70)
    else:
        print("\n✅ NENHUMA HARDCODED CREDENTIAL ENCONTRADA!")
        print("\n🎉 Repo está seguro!")
        print("="*70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python code-guardian-analysis.py <caminho-do-repo>")
        sys.exit(1)
    
    main(sys.argv[1])
