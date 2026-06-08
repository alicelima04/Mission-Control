"""src/telemetria.py — Geração de dados simulados da telemetria.

Trilha: MobilitySat (satélite GNSS de navegação, estilo GPS/Galileo).

Parâmetros monitorados (todos plausíveis, não cientificamente exatos):
  - drift_oscilador_ns   : drift do oscilador atômico em ns/dia. Quanto maior,
                           pior a sincronização de tempo e, por consequência,
                           a precisão de posicionamento na Terra.
  - sync_constelacao_pct : nível de sincronização com a constelação (%).
  - integridade_sinal_pct: integridade dos sinais L1/L5 (%).
  - erro_efemeride_m     : erro de efeméride (órbita reportada vs. real) em metros.
  - margem_potencia_pct  : margem de potência do barramento elétrico (%).

A telemetria é gerada de forma estocástica em torno de valores nominais, com
um "modo de cenário" opcional que permite forçar situações extremas para
demonstração (drift, perda de sync, baixa energia, apagão total).
"""

import json
import random
from datetime import datetime
from pathlib import Path

# Valores nominais (operação saudável) por parâmetro
NOMINAIS = {
    "drift_oscilador_ns": 4.0,      # ns/dia
    "sync_constelacao_pct": 99.0,   # %
    "integridade_sinal_pct": 99.5,  # %
    "erro_efemeride_m": 0.8,        # metros
    "margem_potencia_pct": 72.0,    # %
}

# Ruído aleatório aplicado em cada leitura nominal (±)
RUIDO = {
    "drift_oscilador_ns": 1.5,
    "sync_constelacao_pct": 0.8,
    "integridade_sinal_pct": 0.4,
    "erro_efemeride_m": 0.4,
    "margem_potencia_pct": 4.0,
}

# Cenários pré-definidos para forçar situações de teste/demonstração.
# Sobrescrevem apenas os campos listados; os demais seguem nominais + ruído.
CENARIOS = {
    "normal": {},
    "drift": {"drift_oscilador_ns": 41.0, "erro_efemeride_m": 9.5},
    "sync": {"sync_constelacao_pct": 74.0, "integridade_sinal_pct": 88.0},
    "energia": {"margem_potencia_pct": 14.0},
    "apagao": {
        "drift_oscilador_ns": 55.0,
        "sync_constelacao_pct": 61.0,
        "integridade_sinal_pct": 79.0,
        "erro_efemeride_m": 14.0,
        "margem_potencia_pct": 9.0,
    },
}

# Contador global de ciclos da missão (simula passagem de tempo)
_ciclo = 0

# Cenário ativo no momento (None = geração estocástica normal)
_cenario_ativo = None


def set_cenario(nome):
    """Define o cenário ativo. Retorna o nome aplicado ou None se inválido."""
    global _cenario_ativo
    if nome in CENARIOS:
        _cenario_ativo = None if nome == "normal" else nome
        return nome
    return None


def cenarios_disponiveis():
    """Lista os nomes de cenários que podem ser forçados."""
    return list(CENARIOS.keys())


def _aplica_ruido(base):
    """Aplica ruído gaussiano leve e arredonda."""
    leitura = {}
    for chave, valor in base.items():
        delta = random.uniform(-RUIDO[chave], RUIDO[chave])
        leitura[chave] = round(max(0.0, valor + delta), 2)
    return leitura


def coletar(cenario=None):
    """Coleta uma leitura de telemetria.

    Args:
        cenario: nome de cenário forçado (ver CENARIOS). Se None, usa o
                 cenário ativo definido por set_cenario(), ou geração normal.

    Returns:
        dict com timestamp, ciclo, os 5 parâmetros e o modo de operação.
    """
    global _ciclo
    _ciclo += 1

    nome_cenario = cenario if cenario is not None else _cenario_ativo

    base = dict(NOMINAIS)
    if nome_cenario in CENARIOS and nome_cenario != "normal":
        base.update(CENARIOS[nome_cenario])

    leitura = _aplica_ruido(base)
    leitura["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    leitura["ciclo"] = _ciclo
    leitura["cenario"] = nome_cenario or "normal"
    return leitura


def carregar_cenario_json(caminho="data/cenarios.json"):
    """Carrega cenários extras de um JSON (opcional). Mescla em CENARIOS."""
    path = Path(caminho)
    if not path.exists():
        return False
    try:
        extra = json.loads(path.read_text(encoding="utf-8"))
        CENARIOS.update(extra)
        return True
    except (json.JSONDecodeError, OSError):
        return False


# Rótulos legíveis e unidades para formatação na UI / prompt
ROTULOS = {
    "drift_oscilador_ns": ("Drift do oscilador atômico", "ns/dia"),
    "sync_constelacao_pct": ("Sincronização com a constelação", "%"),
    "integridade_sinal_pct": ("Integridade do sinal L1/L5", "%"),
    "erro_efemeride_m": ("Erro de efeméride", "m"),
    "margem_potencia_pct": ("Margem de potência", "%"),
}


def formatar_legivel(dados):
    """Formata uma leitura de telemetria para texto legível (status/prompt)."""
    linhas = [
        f"Ciclo #{dados['ciclo']} · {dados['timestamp']} · cenário: {dados['cenario']}",
        "",
    ]
    for chave, (rotulo, unidade) in ROTULOS.items():
        linhas.append(f"  • {rotulo}: {dados[chave]} {unidade}")
    return "\n".join(linhas)
