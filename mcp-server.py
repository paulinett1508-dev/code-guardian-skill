"""
Code Guardian MCP Server

Server MCP para integracao com Claude Code.
Permite que o Claude Code chame a skill sem gastar tokens com analise.
"""

import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from main import analyze_repo


# Inicializa server MCP
app = Server("code-guardian")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista ferramentas disponiveis"""
    
    return [
        Tool(
            name="analyze-repo",
            description="Analisa um repositorio em busca de issues de seguranca, compliance, leiturabilidade, UX/UI, performance e aspectos operacionais",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Caminho absoluto para o repositorio a ser analisado"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Diretorio para salvar o diagnostico (opcional, default: ./diagnostico)"
                    },
                    "languages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Linguagens para analisar (opcional, default: todas)"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Modo verbose (opcional, default: false)"
                    }
                },
                "required": ["repo_path"]
            }
        ),
        Tool(
            name="quick-scan",
            description="Scan rapido apenas para issues criticas e altas (seguranca + performance)",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Caminho absoluto para o repositorio"
                    }
                },
                "required": ["repo_path"]
            }
        ),
        Tool(
            name="security-scan",
            description="Scan focado apenas em seguranca (hardcoded credentials, SQL injection, XSS, etc)",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Caminho absoluto para o repositorio"
                    }
                },
                "required": ["repo_path"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Executa ferramenta solicitada"""
    
    try:
        if name == "analyze-repo":
            repo_path = arguments["repo_path"]
            output_dir = arguments.get("output_dir")
            languages = arguments.get("languages")
            verbose = arguments.get("verbose", False)
            
            resultados = analyze_repo(repo_path, output_dir, languages, verbose)
            
            # Retorna resumo
            total_issues = sum(len(r.get("issues", [])) for r in resultados.values())
            critical = sum(
                len([i for i in r.get("issues", []) if i.get("severity") == "critical"])
                for r in resultados.values()
            )
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "total_issues": total_issues,
                        "critical_issues": critical,
                        "categories": list(resultados.keys()),
                        "output_dir": output_dir or str(Path(repo_path) / "diagnostico"),
                        "message": f"Analise completa: {total_issues} issues ({critical} criticas). Veja o diagnostico.json para detalhes."
                    }, indent=2)
                )
            ]
        
        elif name == "quick-scan":
            repo_path = arguments["repo_path"]
            
            # Apenas seguranca e performance
            from analyzers.seguranca import SegurancaAnalyzer
            from analyzers.performance import PerformanceAnalyzer
            
            repo = Path(repo_path)
            
            seg_analyzer = SegurancaAnalyzer(repo, verbose=False)
            perf_analyzer = PerformanceAnalyzer(repo, verbose=False)
            
            seg_result = seg_analyzer.analyze()
            perf_result = perf_analyzer.analyze()
            
            critical_seg = [i for i in seg_result["issues"] if i["severity"] == "critical"]
            high_seg = [i for i in seg_result["issues"] if i["severity"] == "high"]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "scan_type": "quick",
                        "seguranca": {
                            "total": len(seg_result["issues"]),
                            "critical": len(critical_seg),
                            "high": len(high_seg),
                            "top_issues": critical_seg[:5] + high_seg[:5]
                        },
                        "performance": {
                            "total": len(perf_result["issues"]),
                            "top_issues": perf_result["issues"][:5]
                        }
                    }, indent=2, ensure_ascii=False)
                )
            ]
        
        elif name == "security-scan":
            repo_path = arguments["repo_path"]
            
            from analyzers.seguranca import SegurancaAnalyzer
            from analyzers.compliance import ComplianceAnalyzer
            
            repo = Path(repo_path)
            
            seg_analyzer = SegurancaAnalyzer(repo, verbose=False)
            comp_analyzer = ComplianceAnalyzer(repo, verbose=False)
            
            seg_result = seg_analyzer.analyze()
            comp_result = comp_analyzer.analyze()
            
            # Filtra apenas criticas e altas
            critical_high = [
                i for i in seg_result["issues"] + comp_result["issues"]
                if i["severity"] in ["critical", "high"]
            ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "scan_type": "security",
                        "total_issues": len(critical_high),
                        "critical": len([i for i in critical_high if i["severity"] == "critical"]),
                        "high": len([i for i in critical_high if i["severity"] == "high"]),
                        "issues": critical_high
                    }, indent=2, ensure_ascii=False)
                )
            ]
        
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Ferramenta desconhecida: {name}"
                    })
                )
            ]
    
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "type": type(e).__name__
                }, indent=2)
            )
        ]


async def main():
    """Inicia server MCP"""
    
    print("[Code Guardian MCP] Iniciando server...", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
