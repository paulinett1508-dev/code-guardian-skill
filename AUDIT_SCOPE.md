# Code Guardian — Escopo de Auditoria Ampliada

## Propósito

O Code Guardian é uma ferramenta modular de triagem, governança e melhoria contínua de repositórios. Ele não deve se limitar à busca de credenciais hardcoded: deve revelar riscos de segurança, fragilidade técnica, documentação desatualizada, acúmulo de código morto, incoerências arquiteturais e problemas de experiência e governança visual.

A ferramenta produz evidências e recomendações. Nenhuma correção, exclusão, commit ou push pode ocorrer sem revisão e confirmação explícita do usuário.

## Princípios

- **Evidência antes de alteração:** um achado deve indicar regra, arquivo, linha quando possível, severidade e limitação.
- **Não destrutivo por padrão:** auditorias apenas leem arquivos e metadados; correções são propostas separadamente.
- **Contexto antes de julgamento:** um arquivo aparentemente antigo, uma stack secundária ou um script incomum não é lixo sem evidência de que está desconectado do produto.
- **Sem segredo em relatório:** credenciais, URLs sensíveis e conteúdo de variáveis devem ser mascarados.
- **Linguagem clara:** distinguir fato observado, hipótese, alerta e recomendação.
- **Escopo declarado:** “sem achados” significa “sem achados nas regras e arquivos cobertos”, nunca garantia absoluta.
- **Preservação do histórico:** nunca usar `git push --force` sem confirmação explícita.

## Classificação de severidade

| Nível | Significado | Ação esperada |
|---|---|---|
| Crítico | Exposição provável de segredo, execução remota, perda de dados ou produção vulnerável | Interromper publicação e revisar imediatamente |
| Alto | Falha relevante de autenticação, injeção provável, dependência vulnerável ou configuração insegura | Corrigir antes de nova entrega quando viável |
| Médio | Risco técnico, manutenção ou governança com impacto plausível | Planejar correção e registrar decisão |
| Baixo | Inconsistência, dívida técnica localizada ou melhoria de qualidade | Priorizar conforme contexto |
| Informativo | Evidência sem risco comprovado | Revisar quando necessário |

## Domínios de auditoria

### 1. Segurança de segredos e Git

- Credenciais hardcoded, chaves privadas, certificados, tokens, URLs de banco e arquivos `.env` rastreados.
- Segredos em histórico Git recente quando a análise de histórico for solicitada.
- Arquivos sensíveis: `.pem`, `.key`, `.p12`, `.pfx`, `.kdbx`, dumps SQL, backups e arquivos de configuração local.
- Qualidade de `.gitignore`, presença de `.env.example` e documentação segura de variáveis.
- Estado do Git, remoto, branch, commits pendentes, submódulos e arquivos não rastreados relevantes.

### 2. Segurança de código e configuração

- Padrões como `eval`, `exec`, desserialização insegura, `subprocess(shell=True)`, comandos montados com entrada do usuário e SQL concatenado.
- Possíveis XSS: `dangerouslySetInnerHTML`, renderização de HTML sem sanitização e templates perigosos.
- CORS excessivamente permissivo, debug em produção, secrets default, JWT sem expiração ou configuração insegura.
- Cabeçalhos de segurança, cookies, rate limiting e validação de entrada quando aplicável.
- Docker, Compose e infraestrutura: root, imagens `latest`, portas expostas, secrets em build args e permissões amplas.
- GitHub Actions e CI/CD: permissões do token, actions sem pin, comandos com segredos e workflows inseguros.

### 3. Dependências, build e integração

- Manifestos e lockfiles: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `requirements.txt`, `poetry.lock`, `pyproject.toml` e equivalentes.
- Comandos disponíveis de teste, lint, type-check e build; executar apenas o que o projeto declara e o usuário autorizar.
- Auditorias de dependência quando as ferramentas estiverem instaladas e forem autorizadas: `npm audit`, `pip-audit`, entre outras.
- Versões duplicadas, dependências sem uso aparente e ferramentas não conectadas ao pipeline.
- Erros de integração entre pacotes de monorepo, workspaces, submódulos e serviços.

### 4. Arquitetura, monorepos e stacks

- Identificar monorepo, workspaces, submódulos, múltiplas aplicações, bibliotecas e serviços.
- Mapear stacks presentes e seus pontos de entrada: Node, Python, Java, PHP, .NET, frontend estático, Docker e outros.
- Diferenciar stack ativa, ferramenta de suporte, migração em curso, protótipo e possível código morto.
- Detectar múltiplos manifestos, builds concorrentes, configuração duplicada e dependências que conflitam.
- Encontrar pastas desconectadas de qualquer build, import, referência em documentação, pipeline ou deploy.
- Produzir hipóteses de acoplamento, duplicidade e risco; nunca apagar automaticamente.

### 5. Higiene de repositório e código morto

- Arquivos temporários, artefatos gerados, backups, logs, binários e pastas de IDE indevidamente versionados.
- Scripts aleatórios sem referência em `package.json`, Makefile, CI, documentação ou código.
- HTML, protótipos e páginas estáticas sem rota, link, build ou deploy conhecidos.
- Arquivos duplicados, cópias com sufixos como `-old`, `-copy`, `backup`, `final`, `novo` e variações.
- Pastas vazias, arquivos grandes e extensões incomuns em diretórios de aplicação.
- Código não importado ou não referenciado: classificar como “candidato à revisão”, não como descartável.

### 6. Documentação e conformidade documental

- Inventariar `README`, `CONTRIBUTING`, `ARCHITECTURE`, `SECURITY`, `CHANGELOG`, ADRs, runbooks, guias de deploy e documentos de produto.
- Detectar documentação duplicada, contraditória, sem atualização aparente, sem links válidos ou não relacionada a arquivos reais.
- Identificar `README.md` em diretórios sem papel claro, documentação que apenas replica código e arquivos Markdown vazios ou obsoletos.
- Verificar se scripts e comandos documentados existem e se os manifestos descrevem o uso real.
- Verificar coerência entre árvore do repositório, documentação, CI/CD, comandos de instalação e pontos de entrada.
- Verificar Skills, agentes, prompts, configurações de MCP e artefatos de automação que residem no repositório: versão, propósito, instruções, referências e riscos de segurança.
- Produzir uma matriz: documento/artefato, finalidade declarada, referência encontrada, estado e recomendação.

### 7. Design system, UI, UX e governança visual

A análise automatizada não substitui avaliação humana, testes com usuários, auditoria de acessibilidade ou inspeção visual em navegador. Ela deve separar verificações estáticas de recomendações de revisão manual.

#### Verificações estáticas

- Estrutura semântica HTML, presença de `lang`, título, meta viewport, labels e atributos básicos de acessibilidade.
- Imagens sem `alt`, botões sem nome acessível, links vazios, inputs sem label e hierarquia de títulos problemática.
- CSS embutido, estilos inline excessivos e duplicação de estilos entre páginas/componentes.
- HTML/CSS/JS monolítico quando existe framework ou design system declarado.
- Tokens de cor, espaçamento, tipografia e componentes: localizar divergências e valores repetidos que indiquem ausência de governança.
- Uso de cores com contraste potencialmente insuficiente, quando a ferramenta puder calcular a partir de valores estáticos.
- Presença de bibliotecas de UI concorrentes e padrões de componentes inconsistentes.
- Arquivos HTML estáticos sem referência, páginas duplicadas ou estilos que não participam do build.

#### Revisão humana guiada

- Fluxos principais, clareza de navegação, mensagens de erro, feedback de carregamento e estados vazios.
- Consistência visual, responsividade, prioridade de conteúdo, previsibilidade de interação e qualidade percebida.
- Aderência a design system, identidade visual e objetivos reais do produto.
- Evidências devem ser capturadas por screenshots, testes em navegador ou ferramentas próprias, nunca inferidas apenas por texto de código.

### 8. Qualidade operacional

- Testes realmente disponíveis, lint, type-check, build e validação de configuração.
- Scripts que falham, comandos ausentes na documentação e diferença entre ambiente local e CI.
- Portas, variáveis de ambiente, banco de testes e pré-requisitos de execução.
- Observabilidade básica: logs com segredos, ausência de tratamento de erro e mecanismos de health check quando aplicável.

## Módulos propostos

```text
analyzers/
  secrets_analyzer.py
  git_analyzer.py
  environment_analyzer.py
  code_security_analyzer.py
  dependency_analyzer.py
  config_analyzer.py
  ci_cd_analyzer.py
  container_analyzer.py
  architecture_analyzer.py
  repository_hygiene_analyzer.py
  documentation_analyzer.py
  skills_analyzer.py
  ui_static_analyzer.py
  quality_analyzer.py
reporting/
  models.py
  reporter.py
  baseline.py
remediation/
  proposals.py
  apply_approved_fixes.py
```

## Formato mínimo de achado

Cada achado deve conter:

```json
{
  "id": "CG-DOC-001",
  "domain": "documentation",
  "severity": "medium",
  "confidence": "medium",
  "title": "Documento sem referência observada",
  "evidence": {
    "path": "docs/legacy-guide.md",
    "line": null,
    "summary": "Nenhum link, comando, workflow ou referência ao arquivo foi localizado."
  },
  "recommendation": "Revisar com o responsável; atualizar, mover para histórico ou remover somente após confirmação.",
  "limitations": "Análise estática não confirma uso externo ao repositório."
}
```

## Modos de execução

- `quick`: segredos, arquivos sensíveis, Git, manifestos e higiene básica.
- `standard`: quick + código inseguro, ambiente, documentação, arquitetura e UI estática.
- `deep`: standard + histórico Git quando autorizado, dependências, CI/CD, containers, baseline e comandos de qualidade disponíveis.
- `review`: não executa correções; gera lista priorizada para revisão humana.

## Limites explícitos

- Não substitui pentest, SAST comercial, DAST, threat modeling, revisão humana de arquitetura, auditoria de acessibilidade completa ou testes com usuários.
- Não deve decidir sozinho que código, documentos ou scripts são inúteis.
- Não deve executar comandos custosos, de rede, instalação de dependências, testes ou alterações sem informar o usuário e respeitar o modo de execução.
- Não deve publicar resultados, criar commits ou fazer push sem confirmação explícita.

## Roadmap

### Fase A — Fundamento seguro

1. Criar modelos de achado, severidade, confidência e relatórios JSON/Markdown.
2. Refatorar o scanner atual como `secrets_analyzer.py`.
3. Implementar `git_analyzer.py`, `environment_analyzer.py` e `repository_hygiene_analyzer.py`.
4. Atualizar a comunicação para “sem achados no escopo”, não “repo seguro”.

### Fase B — Mapa do repositório

1. Implementar descoberta de monorepo, stacks, manifestos, submódulos e pontos de entrada.
2. Implementar análise documental e de Skills/automação residentes no repositório.
3. Gerar inventário e matriz de referências antes de classificar algo como obsoleto.

### Fase C — Segurança e entrega

1. Implementar análise de padrões perigosos por linguagem.
2. Implementar dependências, CI/CD, containers e configurações de runtime.
3. Integrar validações de build/test/lint somente quando declaradas pelo projeto.

### Fase D — Governança visual

1. Implementar análise estática de HTML, CSS, acessibilidade básica e design tokens.
2. Identificar estilos inline, HTML estático desconectado, bibliotecas concorrentes e inconsistências de tokens.
3. Criar checklist de revisão humana para UX/UI, responsividade, estados e consistência visual.

### Fase E — Correção assistida

1. Gerar propostas de patch por achado confirmado.
2. Exigir aprovação por arquivo e por tipo de alteração.
3. Revalidar, apresentar diff e separar commit local de push remoto.

## Critério de sucesso

Uma execução do Code Guardian deve deixar claro:

1. O que foi analisado e o que ficou fora do escopo.
2. Quais achados são comprovados, quais são hipóteses e quais exigem revisão humana.
3. Quais arquivos e fluxos parecem ativos, legados ou desconectados.
4. Quais ações são recomendadas, sem alterações automáticas não autorizadas.
5. O estado local do Git, os commits locais e o estado publicado no remoto.
