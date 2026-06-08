"""src/alertas.py — Thresholds, regras de decisão e respostas automatizadas.

Toda a lógica de "isto é crítico ou não" mora AQUI, em Python — não no
prompt da IA. O LLM serve para explicar e contextualizar os alertas, nunca
para decidir se algo é crítico (isso seria inconsistente).

Cada parâmetro tem dois limiares: atenção (amarelo) e crítico (vermelho).
A função avaliar() devolve um dicionário estruturado com a lista de alertas,
o nível geral da missão e as ações automatizadas disparadas.
"""

# Limiares por parâmetro.
# direcao "alto" => valores ALTOS são ruins; "baixo" => valores BAIXOS são ruins.
THRESHOLDS = {
    "drift_oscilador_ns": {
        "direcao": "alto",
        "atencao": 15.0,
        "critico": 30.0,
        "impacto": "Erro de relógio degrada a triangulação: posicionamento de "
                   "frotas e plantadeiras autônomas perde precisão (metros viram dezenas de metros).",
    },
    "sync_constelacao_pct": {
        "direcao": "baixo",
        "atencao": 95.0,
        "critico": 85.0,
        "impacto": "Sem sincronização entre satélites, o receptor não fecha solução "
                   "de posição confiável — rotas logísticas e operações de campo ficam às cegas.",
    },
    "integridade_sinal_pct": {
        "direcao": "baixo",
        "atencao": 96.0,
        "critico": 92.0,
        "impacto": "Sinais L1/L5 corrompidos comprometem a integridade exigida por "
                   "veículos autônomos e aviação — risco de posição errada sem aviso.",
    },
    "erro_efemeride_m": {
        "direcao": "alto",
        "atencao": 3.0,
        "critico": 8.0,
        "impacto": "Órbita reportada divergente da real injeta erro sistemático na "
                   "posição de todos os usuários do satélite ao mesmo tempo.",
    },
    "margem_potencia_pct": {
        "direcao": "baixo",
        "atencao": 25.0,
        "critico": 18.0,
        "impacto": "Pouca energia força desligamento de cargas — risco de perder a "
                   "transmissão do sinal de navegação para a região coberta.",
    },
}

NIVEIS_ORDEM = {"normal": 0, "atencao": 1, "critico": 2}


def _classificar(chave, valor):
    """Classifica um único parâmetro em normal / atencao / critico."""
    regra = THRESHOLDS[chave]
    if regra["direcao"] == "alto":
        if valor >= regra["critico"]:
            return "critico"
        if valor >= regra["atencao"]:
            return "atencao"
    else:  # direcao == "baixo"
        if valor <= regra["critico"]:
            return "critico"
        if valor <= regra["atencao"]:
            return "atencao"
    return "normal"


def _acoes_automatizadas(dados, alertas_criticos):
    """Respostas automatizadas em código diante de situações críticas.

    Cada ação é uma decisão tomada SEM a IA — lógica pura de bordo.
    Retorna uma lista de strings descrevendo o que o sistema 'executou'.
    """
    acoes = []
    params_criticos = {a["parametro"] for a in alertas_criticos}

    if "margem_potencia_pct" in params_criticos:
        acoes.append(
            "MODO ECONOMIA ativado: cargas não essenciais desligadas para "
            "preservar a transmissão do sinal de navegação."
        )
    if "drift_oscilador_ns" in params_criticos:
        acoes.append(
            "Comutação para OSCILADOR REDUNDANTE solicitada e flag de "
            "integridade de tempo levantada aos receptores."
        )
    if "sync_constelacao_pct" in params_criticos:
        acoes.append(
            "RAIM acionado: satélite marcado como 'não-utilizável' até "
            "ressincronizar; receptores priorizam outras constelações."
        )
    if "erro_efemeride_m" in params_criticos:
        acoes.append(
            "Upload de efeméride corrigida agendado na próxima janela de "
            "contato com o segmento de controle terrestre."
        )
    return acoes


def avaliar(dados):
    """Avalia uma leitura de telemetria e retorna o diagnóstico estruturado.

    Returns:
        dict com:
          - alertas: lista de {parametro, rotulo, valor, severidade, mensagem, impacto}
          - nivel_geral: "normal" | "atencao" | "critico"
          - acoes_automatizadas: lista de strings
    """
    from src.telemetria import ROTULOS

    alertas = []
    nivel_geral = "normal"

    for chave in THRESHOLDS:
        if chave not in dados:
            continue
        valor = dados[chave]
        severidade = _classificar(chave, valor)
        if NIVEIS_ORDEM[severidade] > NIVEIS_ORDEM[nivel_geral]:
            nivel_geral = severidade
        if severidade != "normal":
            rotulo, unidade = ROTULOS[chave]
            alertas.append(
                {
                    "parametro": chave,
                    "rotulo": rotulo,
                    "valor": f"{valor} {unidade}",
                    "severidade": severidade,
                    "mensagem": f"{rotulo} em nível {severidade.upper()} ({valor} {unidade}).",
                    "impacto": THRESHOLDS[chave]["impacto"],
                }
            )

    criticos = [a for a in alertas if a["severidade"] == "critico"]
    acoes = _acoes_automatizadas(dados, criticos)

    return {
        "alertas": alertas,
        "nivel_geral": nivel_geral,
        "acoes_automatizadas": acoes,
    }


def formatar_legivel(diagnostico):
    """Formata o diagnóstico para texto (usado no /status e no prompt)."""
    nivel = diagnostico["nivel_geral"]
    simbolo = {"normal": "🟢", "atencao": "🟡", "critico": "🔴"}[nivel]
    linhas = [f"{simbolo} Nível geral da missão: {nivel.upper()}"]

    if not diagnostico["alertas"]:
        linhas.append("  Todos os parâmetros dentro do range nominal.")
    else:
        linhas.append("  Alertas ativos:")
        for a in diagnostico["alertas"]:
            marca = "🔴" if a["severidade"] == "critico" else "🟡"
            linhas.append(f"   {marca} {a['mensagem']}")

    if diagnostico["acoes_automatizadas"]:
        linhas.append("  Ações automáticas executadas:")
        for acao in diagnostico["acoes_automatizadas"]:
            linhas.append(f"   ⚙ {acao}")

    return "\n".join(linhas)
