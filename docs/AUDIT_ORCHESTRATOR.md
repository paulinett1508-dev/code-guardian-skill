# Audit Orchestrator

Este documento descreve o orquestrador de auditoria de repositório do Code Guardian Toolkit.

## Visão geral

O script `audit-repository.py` realiza uma auditoria de segurança em modo leitura, focada em:

- detectar credenciais hardcoded e configurações inseguras;
- verificar a cobertura do `.gitignore` para arquivos sensíveis;
- identificar caminhos sensíveis rastreados no Git;
- mapear a stack do projeto (Node, PHP, Python, Docker, Playwright etc.);
- descobrir scripts declarados em `package.json` (sem executá-los).

O objetivo é substituir a execução manual de múltiplos comandos por um único ponto de entrada, gerando relatórios JSON e Markdown sanitizados.

## Uso

```powershell
python audit-repository.py `
  'D:\caminho\para\repositorio' `
  --report-dir 'D:\AUDITORIAS\hospital360-v2'
```

Parâmetros:

- `repo_path`: caminho absoluto do repositório Git a auditar.
- `--report-dir`: diretório onde os relatórios serão gravados (fora do repositório auditado).

## Comportamento e salvaguardas

- Modo leitura: não faz `fetch`, `pull`, `commit`, `push`, `issue` ou PR.
- Não cria, sobrescreve ou lê `.env`.
- Não inicia Docker, banco, aplicação ou navegador.
- Não executa scripts do repositório auditado.
- Gera relatórios fora do repositório auditado.
- Nunca persiste o valor potencialmente secreto no relatório.
- Ignora arquivos binários e arquivos maiores que 1 MB.
- Não lê arquivos ignorados pelo `.gitignore`.

## Saída

O script gera dois arquivos:

- `audit-<data>-<repo>.json`: estrutura completa da auditoria.
- `audit-<data>-<repo>.md`: relatório legível em Markdown.

Códigos de saída:

- `0`: nenhum achado suspeito/alto risco;
- `1`: achados suspeitos ou alto risco;
- `2`: execução bloqueada/erro de configuração.

## Limitações

- A auditoria não é exaustiva: "nenhum achado" não é garantia absoluta.
- Arquivos ignorados e binários não são escaneados.
- O script não substitui testes E2E, SAST avançado ou revisão humana.

## Próximos passos sugeridos

- Integrar este script em pipelines de CI/CD como etapa de gate.
- Usar os relatórios como base para correções pontuais com `fix-hardcoded-creds.py` e `finalize-fix.py`.
- Evoluir os padrões de detecção conforme novos vetores forem identificados.
