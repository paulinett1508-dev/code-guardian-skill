#!/usr/bin/env python3
"""
Code Guardian — Fix: Hardcoded Credentials

Propõe (e, com --apply, aplica) a remoção de credenciais hardcoded,
substituindo por leitura de variável de ambiente na sintaxe correta
da linguagem do próprio arquivo.

Por padrão roda em dry-run: mostra o diff proposto e não escreve nada.
Arquivos de teste/fixture (fixture sintética exigida por schema, senha
de teste, etc.) são reportados como INFORMATIVO e nunca reescritos
automaticamente — não são credencial real vazada.

Ver AUDIT_SCOPE.md: "Não destrutivo por padrão" e "Nenhuma correção...
pode ocorrer sem revisão e confirmação explícita do usuário".

Execute:
  python fix-hardcoded-creds.py <repo> --apply
"""

import argparse
import re
import sys
from pathlib import Path

# Diretorios/arquivos cujo conteudo e fixture de teste, nao segredo real.
# Fixture de teste = constante sintetica exigida por schema/validacao ou
# default de dispositivo local; nao ha segredo de producao para vazar.
TEST_PATH_MARKERS = ("/test/", "/tests/", "/__tests__/", "/spec/", "/fixtures/")
TEST_FILENAME_MARKERS = (".test.", ".spec.", "factories.", "env-setup.", "seed.")

# language -> (regex de leitura ja correta, template de substituicao)
LANG_BY_EXT = {
    ".py": {
        "already_ok": re.compile(r"os\.environ\.get\("),
        "template": lambda var: f'os.environ.get("{var}", "")',
    },
    ".ts": {
        "already_ok": re.compile(r"process\.env\.[A-Z_]+"),
        "template": lambda var: f'process.env.{var} || ""',
    },
    ".js": {
        "already_ok": re.compile(r"process\.env\.[A-Z_]+"),
        "template": lambda var: f'process.env.{var} || ""',
    },
}

# Regex generica de "NOME_QUALQUER = 'valor'" — a decisao de "e credencial?"
# vem do KEYWORDS_BY_LABEL, que casa por substring no nome da variavel
# (pega tambem DB_PASSWORD, INTERNAL_API_KEY, etc, nao so o nome exato).
ASSIGNMENT_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*["\']([^"\']+)["\']')

KEYWORDS_BY_LABEL = [
    (("password", "passwd", "pwd", "senha"), "Senha hardcoded"),
    (("api_key", "apikey", "secret_key"), "API Key hardcoded"),
    (("token",), "Token hardcoded"),
]


def classify(var_name: str):
    lowered = var_name.lower()
    for keywords, label in KEYWORDS_BY_LABEL:
        if any(k in lowered for k in keywords):
            return label
    return None


def is_test_fixture(file_path: Path) -> bool:
    posix = file_path.as_posix().lower()
    if any(marker in posix for marker in TEST_PATH_MARKERS):
        return True
    return any(marker in file_path.name.lower() for marker in TEST_FILENAME_MARKERS)


def propose_fix(file_path: Path, repo_path: Path):
    """Retorna (mudou, conteudo_novo, lista_de_fixes) sem escrever nada."""
    lang = LANG_BY_EXT.get(file_path.suffix)
    if lang is None:
        return False, None, [], "linguagem-nao-suportada"

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Erro ao ler {file_path.name}: {e}")
        return False, None, [], "erro-leitura"

    if is_test_fixture(file_path):
        return False, None, [], "fixture-de-teste"

    original = content
    fixes = []
    for match in re.finditer(ASSIGNMENT_RE, content):
        var_name = match.group(1)
        label = classify(var_name)
        if label is None:
            continue
        env_var = var_name.upper()
        replacement = f"{var_name} = {lang['template'](env_var)}"
        content = content.replace(match.group(0), replacement)
        fixes.append(f"{label}: {env_var}")

    if content == original:
        return False, None, [], "sem-mudanca"
    return True, content, fixes, "proposta"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    parser.add_argument("files", nargs="*", help="Arquivos especificos (default: os do diagnostico mais recente)")
    parser.add_argument("--apply", action="store_true", help="Escreve as mudancas. Sem essa flag, so mostra o diff proposto.")
    args = parser.parse_args()

    repo = Path(args.repo_path)
    if not repo.exists():
        print(f"ERRO: Repo não encontrado em {repo}")
        sys.exit(1)

    files_to_check = [repo / f for f in args.files] if args.files else []
    if not files_to_check:
        print("Nenhum arquivo passado. Uso: fix-hardcoded-creds.py <repo> <arquivo1> [arquivo2 ...] [--apply]")
        sys.exit(1)

    print("Code Guardian — Fix: Hardcoded Credentials")
    print(f"Modo: {'APLICANDO' if args.apply else 'DRY-RUN (nada sera escrito)'}")
    print("=" * 70)

    applied = skipped_fixture = 0

    for file_path in files_to_check:
        if not file_path.exists():
            print(f"Arquivo não encontrado: {file_path}")
            continue

        changed, new_content, fixes, status = propose_fix(file_path, repo)

        if status == "fixture-de-teste":
            print(f"\n[INFORMATIVO] {file_path.relative_to(repo)}")
            print("   Fixture de teste — não é credencial real, não será alterado.")
            skipped_fixture += 1
            continue

        if status == "linguagem-nao-suportada":
            print(f"\n[SKIP] {file_path.relative_to(repo)} — linguagem sem template de fix ({file_path.suffix})")
            continue

        if not changed:
            print(f"\n[OK] {file_path.relative_to(repo)} — nenhuma credencial hardcoded encontrada")
            continue

        print(f"\n[ACHADO] {file_path.relative_to(repo)}")
        for fix in fixes:
            print(f"   - {fix}")

        if args.apply:
            file_path.write_text(new_content, encoding="utf-8")
            print("   Aplicado.")
            applied += 1
        else:
            print("   (dry-run — rode de novo com --apply para escrever)")

    print("\n" + "=" * 70)
    print(f"Resumo: {applied} arquivo(s) alterado(s), {skipped_fixture} fixture(s) de teste ignorada(s)")
    if not args.apply and applied == 0:
        print("Nada foi escrito (dry-run). Revise antes de rodar com --apply.")


if __name__ == "__main__":
    main()
