#!/bin/bash

# Code Guardian Skill - Install Script
# Instala a skill e configura o MCP Server para Claude Code

set -e

echo "🛡️ Code Guardian Skill - Instalacao"
echo "===================================="
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nao encontrado. Instale Python 3.10+ primeiro."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION detectado"

# Cria venv
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
    echo "✅ venv criado"
else
    echo "✅ venv ja existe"
fi

# Ativa venv
source venv/bin/activate

# Instala dependencias
echo ""
echo "📦 Instalando dependencias..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependencias instaladas"

# Instala em modo editavel
echo ""
echo "📦 Instalando code-guardian-skill em modo editavel..."
pip install -e . > /dev/null 2>&1
echo "✅ Skill instalada"

# Configura MCP
echo ""
echo "🔌 Configurando MCP Server..."

# Detecta OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CLAUDE_CONFIG="$HOME/.config/Claude/claude.json"
else
    echo "⚠️ OS nao suportado automaticamente. Configure manualmente."
    CLAUDE_CONFIG=""
fi

if [ -n "$CLAUDE_CONFIG" ]; then
    # Cria diretorio se nao existir
    mkdir -p "$(dirname "$CLAUDE_CONFIG")"
    
    # Backup
    if [ -f "$CLAUDE_CONFIG" ]; then
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.bak"
        echo "✅ Backup criado: $CLAUDE_CONFIG.bak"
    fi
    
    # Adiciona MCP server
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    python3 << EOF
import json

config_file = "$CLAUDE_CONFIG"
script_dir = "$SCRIPT_DIR"

# Le config existente ou cria novo
try:
    with open(config_file, 'r') as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = {}

# Adiciona MCP server
if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['code-guardian'] = {
    'command': 'python3',
    'args': [f'{script_dir}/mcp-server.py'],
    'cwd': script_dir
}

# Salva config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ MCP server configurado em {config_file}")
EOF
fi

# Cria alias
echo ""
echo "📦 Criando alias..."

if ! grep -q "alias code-guardian" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Code Guardian Skill" >> ~/.bashrc
    echo "alias code-guardian='cd $SCRIPT_DIR && source venv/bin/activate && python main.py'" >> ~/.bashrc
    echo "✅ Alias adicionado ao ~/.bashrc"
else
    echo "✅ Alias ja existe no ~/.bashrc"
fi

if ! grep -q "alias code-guardian" ~/.zshrc 2>/dev/null; then
    echo "" >> ~/.zshrc
    echo "# Code Guardian Skill" >> ~/.zshrc
    echo "alias code-guardian='cd $SCRIPT_DIR && source venv/bin/activate && python main.py'" >> ~/.zshrc
    echo "✅ Alias adicionado ao ~/.zshrc"
else
    echo "✅ Alias ja existe no ~/.zshrc"
fi

echo ""
echo "===================================="
echo "✅ Instalacao concluida!"
echo ""
echo "📝 Uso:"
echo "   1. Reinicie o terminal ou: source ~/.bashrc (ou ~/.zshrc)"
echo "   2. code-guardian /path/to/repo"
echo ""
echo "🔌 No Claude Code:"
echo "   A skill ja esta disponivel via MCP. Use:"
echo "   - analyze-repo: analise completa"
echo "   - quick-scan: scan rapido (seguranca + performance)"
echo "   - security-scan: apenas seguranca"
echo ""
echo "===================================="
