"""Interface CLI estilo Claude Code — usa Rich + prompt-toolkit.

Camada de apresentação da Mission Control AI. Esta camada NÃO contém
lógica de domínio: ela apenas exibe o banner, gerencia o loop de input
e despacha cada pergunta para `engine.analyze()`. Toda a inteligência
mora em src/engine.py, src/telemetria.py e src/alertas.py.
"""

from datetime import datetime

import pyfiglet
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()
session = PromptSession(style=Style.from_dict({"prompt": "#06B6D4 bold"}))

# Paleta da trilha MobilitySat (azul GNSS / ciano sinal)
COR_PRIMARIA = "#06B6D4"
COR_DESTAQUE = "#A855F7"


def show_banner():
    """Exibe o banner ASCII colorido no início."""
    banner = pyfiglet.figlet_format("Mission Control", font="ansi_shadow")
    console.print(Text(banner, style=f"bold {COR_PRIMARIA}"))
    console.print(
        Panel.fit(
            "Bem-vindo à interface da [bold]Mission Control AI[/bold] — Trilha [bold cyan]MobilitySat (GNSS)[/bold cyan].\n"
            "Monitoramento e análise de telemetria de satélite de navegação por IA generativa.\n"
            "Use [bold]/help[/bold] para ver os comandos · [bold]/exit[/bold] para sair.\n"
            "Modelo: [italic]gpt-oss:120b[/italic] via Ollama Cloud",
            title="◆ MISSION CONTROL",
            subtitle="connected",
            border_style=COR_PRIMARIA,
        )
    )


def show_response(text, titulo="◆ Mission Control"):
    """Renderiza a resposta da IA em um painel com timestamp."""
    now = datetime.now().strftime("%H:%M")
    console.print(
        Panel(text, title=titulo, subtitle=now, border_style=COR_PRIMARIA)
    )


def show_help():
    """Mostra a tabela de comandos disponíveis."""
    from rich.table import Table

    tabela = Table(title="Comandos disponíveis", border_style=COR_DESTAQUE)
    tabela.add_column("Comando", style="bold cyan")
    tabela.add_column("Descrição")
    tabela.add_row("/help", "Mostra esta lista de comandos")
    tabela.add_row("/status", "Snapshot atual da telemetria + alertas ativos")
    tabela.add_row("/cenario <nome>", "Força um cenário: normal | drift | sync | energia | apagao")
    tabela.add_row("/about", "Sobre o sistema e a trilha")
    tabela.add_row("/clear", "Limpa a tela e reexibe o banner")
    tabela.add_row("/exit", "Encerra a sessão")
    tabela.add_row("<pergunta>", "Qualquer texto vira uma análise da IA sobre a missão")
    console.print(tabela)


def show_about():
    """Texto institucional sobre o projeto."""
    show_response(
        "[bold]Mission Control AI — MobilitySat[/bold]\n\n"
        "Sistema de monitoramento operacional de um satélite GNSS (estilo GPS/Galileo).\n"
        "Detecta anomalias via lógica Python (thresholds + decisão) e usa um LLM para\n"
        "traduzir cada anomalia em impacto terrestre: frotas logísticas, agricultura de\n"
        "precisão e bases de veículos autônomos.\n\n"
        "FIAP · Ciência da Computação · Global Solution 2026.1",
        titulo="◆ Sobre",
    )


def run_cli(engine):
    """Loop principal da CLI."""
    show_banner()
    if not engine.is_ready():
        console.print(
            " ⚠ Engine status: AGUARDANDO IMPLEMENTAÇÃO ✗\n", style="yellow"
        )
    else:
        console.print(" ✓ Engine status: OPERACIONAL\n", style="green")

    while True:
        try:
            user_input = session.prompt("❯ ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        if user_input == "/exit":
            console.print("Encerrando Mission Control. Até logo! 🛰", style=COR_PRIMARIA)
            break

        if user_input == "/help":
            show_help()
            continue

        if user_input == "/about":
            show_about()
            continue

        if user_input == "/status":
            show_response(engine.status_snapshot(), titulo="◆ Status da Missão")
            continue

        if user_input.startswith("/cenario"):
            partes = user_input.split(maxsplit=1)
            nome = partes[1].strip() if len(partes) > 1 else ""
            msg = engine.set_cenario(nome)
            console.print(msg, style="yellow")
            continue

        if user_input == "/clear":
            console.clear()
            show_banner()
            continue

        # Qualquer outra entrada vai para o motor de análise.
        with console.status("[cyan]Analisando telemetria com a IA...", spinner="dots"):
            resposta = engine.analyze(user_input)
        show_response(resposta)
