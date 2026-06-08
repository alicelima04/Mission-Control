"""banner_ascii.py — Gerador de banner ASCII art da Mission Control AI.

Script auxiliar standalone para experimentar fontes do PyFiglet e
customizar o banner do projeto.

Uso:
    $ python banner_ascii.py                       # banner padrão
    $ python banner_ascii.py -fonts                # lista as 570+ fontes
    $ python banner_ascii.py -font slant -text "Mission Control AI"
    $ python banner_ascii.py -demo                 # 8 fontes lado a lado
"""

import sys

import pyfiglet
from rich.align import Align
from rich.console import Console
from rich.text import Text

console = Console()


def banner_padrao():
    """Banner oficial em duas linhas, estilo Claude Code (ciano)."""
    linha1 = pyfiglet.figlet_format("Global Solution", font="ansi_shadow")
    linha2 = pyfiglet.figlet_format("Mission Control AI", font="ansi_shadow")
    console.print(Align.center(Text(linha1, style="bold #A855F7")))
    console.print(Align.center(Text(linha2, style="bold #06B6D4")))
    console.print(
        Align.center(
            Text(
                "── 2026.1 · Prompt Engineering and AI · FIAP ──",
                style="italic #8484A0",
            )
        )
    )


def listar_fontes():
    fontes = pyfiglet.FigletFont.getFonts()
    console.print(f"[bold]{len(fontes)} fontes disponíveis no PyFiglet:[/bold]\n")
    console.print(", ".join(sorted(fontes)))


def testar_fonte(fonte, texto):
    try:
        arte = pyfiglet.figlet_format(texto, font=fonte)
        console.print(Text(arte, style="bold #06B6D4"))
    except pyfiglet.FontNotFound:
        console.print(f"[red]Fonte '{fonte}' não encontrada.[/red] Use -fonts para listar.")


def demo():
    fontes = ["ansi_shadow", "slant", "standard", "big", "doom", "banner3", "cyberlarge", "small"]
    for f in fontes:
        console.print(f"[bold magenta]── {f} ──[/bold magenta]")
        try:
            console.print(Text(pyfiglet.figlet_format("Mission Control AI", font=f), style="#06B6D4"))
        except pyfiglet.FontNotFound:
            console.print(f"[red](fonte {f} indisponível)[/red]")


def main():
    args = sys.argv[1:]
    if not args:
        banner_padrao()
    elif args[0] == "-fonts":
        listar_fontes()
    elif args[0] == "-demo":
        demo()
    elif args[0] == "-font":
        fonte = args[1] if len(args) > 1 else "ansi_shadow"
        texto = "Mission Control AI"
        if "-text" in args:
            texto = args[args.index("-text") + 1]
        testar_fonte(fonte, texto)
    else:
        banner_padrao()


if __name__ == "__main__":
    main()
