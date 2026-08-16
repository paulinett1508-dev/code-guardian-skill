# 🛡️ Code Guardian Skill

**Skill de análise automatizada de código para Claude Code** — **anti-desperdicio de tokens**.

## 🎯 Objetivo

Automatizar análises de código para que o **Claude Code não precise gastar tokens** com jobs básicos, permitindo que você foque no que realmente importa.

### Como funciona?

```
┌─────────────────────────────────────────────────────────┐
│              VS Code + Claude Code                      │
│  (vocêºº: "analisa esse repo")                         │
│                        ↓                                │
│  Claude Code → chama MCP Server → Code Guardian        │
│                        ↓                                │
│  Code Guardian roda LOCAL → retorna JSON               │
│                        ↓                                │
│  Claude Code só gasta tokens APRESENTANDO resultado    │
└─────────────────────────────────────────────────────────┘
```

**Resultado:** Zero tokens de análise — só tokens de apresentação!

---

## 🔍 Módulos de Aná´´lise

| Módulo | O que analisa | Exemplos |
|--------|---------------|----------|
| **Seguranca** | Vulnerabilidades | Hardcoded credentials, SQL injection, XSS, eval() |
| **Compliance** | Conformidade | LGPD, licencas, logs com dados sensiveis |
| **Leiturabilidade** | Qualidade do código | Funcoes longas, magic numbers, nomes obscuros |
| **Navegabilidade** | Estrutura | Diretorios confusos, modulos gigantes |
| **UX/UI** | Frontend | Acessibilidade, loading states, responsividade |
| **Performance** | Performance | N+1 queries, loops aninhados, assets grandes |
| **Operacional** | Ops | Health checks, logging, timeouts, Docker |

---

## 🚀 Instalacao Rapida

### 1. Clone o repositorio

```bash
git clone https://github.com/paulinett1508-dev/code-guardian-skill.git
cd code-guardian-skill
```

### 2. Execute o script de instalacao

```bash
chmod +x install.sh
./install.sh
```

O script vai:
- Criar ambiente virtual
- Instalar dependencias
- Configurar MCP Server no Claude
- Criar alias `code-guardian`

### 3. Manual (se preferir)

```bash
# Cria venv
python3 -m venv venv
source venv/bin/activate

# Instala
pip install -e .

# Configura MCP no Claude (veja abaixo)
```

---

## 🔌 Configuracao MCP no Claude Code

### Opcao 1: Automatica (via install.sh)

O script `install.sh` configura automaticamente se detectar:
- **macOS:** `~/Library/Application Support/Claude/claude.json`
- **Linux:** `~/.config/Claude/claude.json`

### Opcao 2: Manual

Edite seu `claude.json`:

```json
{
  "mcpServers": {
    "code-guardian": {
      "command": "python3",
      "args": ["/path/to/code-guardian-skill/mcp-server.py"],
      "cwd": "/path/to/code-guardian-skill"
    }
  }
}
```

**Onde encontrar claude.json:**
- **macOS:** `~/Library/Application Support/Claude/claude.json`
- **Linux:** `~/.config/Claude/claude.json`
- **Windows:** `%APPDATA%\Claude\claude.json`

---

## 📝 Uso

### Via CLI (terminal)

```bash
# Analise completa
code-guardian /path/to/seu/repo

# Com output customizado
code-guardian /path/to/repo -o ./meu-diagnostico

# Apenas linguagens especificas
code-guardian /path/to/repo -l py js ts

# Modo verbose
code-guardian /path/to/repo -v
```

### Via Claude Code (MCP)

No terminal do VS Code com Claude Code:

```
# Analise completa
Use a ferramenta analyze-repo com repo_path="/path/to/repo"

# Scan rapido (seguranca + performance)
Use quick-scan com repo_path="/path/to/repo"

# Apenas seguranca
Use security-scan com repo_path="/path/to/repo"
```

**Exemplo de prompt:**

```
Analisa o repo /home/user/meu-projeto com code-guardian e me mostra
as issues criticas de seguranca
```

---

## 📊 Output

A skill gera:

### 1. `diagnostico.md` — Relatorio em Markdown

```markdown
# 🛡️ Code Guardian — Diagnostico de Codigo

**Data:** 16/08/2026 11:30
**Repositorio:** /path/to/repo

## 📊 Resumo Geral

| Metrica | Valor |
|---------|-------|
| Total de Issues | 42 |
| Criticas | 3 |
| Altas | 8 |

## 🔍 Seguranca

| Severidade | Tipo | Arquivo | Linha | Mensagem |
|------------|------|---------|-------|----------|
| 🔴 critical | hardcoded_credentials | config.py | 15 | Credencial hardcoded |
```

### 2. `diagnostico.json` — JSON para integracao

```json
{
  "metadata": {
    "generated_at": "2026-08-16T11:30:00",
    "repo": "/path/to/repo"
  },
  "resultados": {
    "seguranca": {
      "issues": [...],
      "summary": {...}
    }
  }
}
```

---

## 🛠️ Ferramentas MCP

| Ferramenta | Descricao |
|------------|----------|
| `analyze-repo` | Analise completa (7 categorias) |
| `quick-scan` | Scan rapido (seguranca + performance) |
| `security-scan` | Apenas seguranca e compliance |

---

## 📁 Estrutura do Projeto

```
code-guardian-skill/
├── analyzers/              # Modulos de analise
│   ├── __init__.py
│   ├── seguranca.py
│   ├── compliance.py
│   ├── leiturabilidade.py
│   ├── navegabilidade.py
│   ├── ux_ui.py
│   ├── performance.py
│   └── operacional.py
├── utils/                  # Utilitarios
│   ├── __init__.py
│   └── reporter.py
├── tests/                  # Testes (TODO)
├── main.py                 # Entry point CLI
├── mcp-server.py           # MCP Server
├── setup.py                # Package setup
├── install.sh              # Script de instalacao
├── requirements.txt        # Dependencias
├── .gitignore
├── claude-mcp-config.example.json
└── README.md
```

---

## 🔧 Desenvolvimento

### Rodando testes (TODO)

```bash
pytest tests/
```

### Adicionando novos analyzers

1. Crie `analyzers/seu_analyzer.py`
2. Implemente a interface:

```python
class SeuAnalyzer:
    nome = "SeuAnalyzer"
    categoria = "sua_categoria"
    
    def __init__(self, repo_path, languages=None, verbose=False):
        self.repo_path = repo_path
        self.issues = []
    
    def analyze(self) -> dict:
        # Sua logica aqui
        return {
            "categoria": self.categoria,
            "issues": self.issues,
            "summary": {...}
        }
```

3. Adicione em `analyzers/__init__.py`
4. Adicione em `main.py`

---

## 🚨 Limitacoes Atuais

- **Patterns estaticos:** A analise de seguranca usa regex (pode ter falsos positivos/negativos)
- **Multi-linguagem limitado:** Focado em Python, JS, TS, PHP
- **Sem AST parsing avancado:** Tree-sitter é opcional
- **UX/UI basico:** Analise de CSS/HTML simplificada

**Contribuicoes sao bem-vindas!** 🎉

---

## 📝 Licenca

MIT — use livremente nos seus projetos.

---

**Criado por:** @paulinett1508-dev  
**Versao:** 0.1.0  
**Repo:** [github.com/paulinett1508-dev/code-guardian-skill](https://github.com/paulinett1508-dev/code-guardian-skill)
