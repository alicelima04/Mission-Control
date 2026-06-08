"""Mission Control AI — ponto de entrada do sistema.

Trilha: MobilitySat (GNSS e Mobilidade)
"""

from src.ui import run_cli
from src.engine import MissionEngine


if __name__ == "__main__":
    engine = MissionEngine()
    run_cli(engine)
