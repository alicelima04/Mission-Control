"""src/engine.py — Motor de análise da Mission Control AI.

Combina:
  (a) a função llm() — ponto ÚNICO de contato com o modelo (seção 4.2/6.4);
  (b) a classe MissionEngine — orquestra telemetria + alertas + IA.

Diferenciais implementados:
  • Memória de contexto: o motor guarda os últimos ciclos e injeta um resumo
    no prompt, dando à IA "consciência temporal" da missão.
  • Few-shot prompting: exemplos de análise ficam no system_prompt.md.
"""

import os
from collections import deque
from pathlib import Path

from dotenv import load_dotenv
from ollama import Client

from src import alertas, telemetria

load_dotenv()

# Identificação da trilha — ALTERE conforme a escolha do grupo.
TRILHA = "mobilitysat"  # "agrosat" | "envirosat" | "connectsat" | "mobilitysat"

client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.environ.get("OLLAMA_API_KEY", "")},
)

api = os.environ.get("OLLAMA_API_KEY")
print("API KEY carregada:", "OK" if api else "FALTANDO")


def llm(prompt, system=None, max_tokens=800, temperature=0.3):
    """Envia prompt ao gpt-oss:120b via Ollama Cloud e retorna texto."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        return client.chat(
            model="gpt-oss:120b",
            messages=messages,
            options={"num_predict": max_tokens, "temperature": temperature},
            stream=False,
        )["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Erro ao consultar IA: {e}"


def load_system_prompt():
    """Lê o system prompt do arquivo prompts/system_prompt.md."""
    path = Path("prompts/system_prompt.md")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Você é um assistente."  # fallback genérico


class MissionEngine:
    """Motor de análise — telemetria + alertas + IA generativa."""

    def __init__(self):
        self.trilha = TRILHA
        self.system_prompt = load_system_prompt()
        # Memória de contexto: últimos 5 ciclos (dados + diagnóstico).
        self.historico = deque(maxlen=5)
        # Carrega cenários extras do JSON, se existir.
        telemetria.carregar_cenario_json()

    def is_ready(self):
        """Engine implementado e operacional."""
        return True

    def set_cenario(self, nome):
        """Força um cenário de telemetria (para demonstração)."""
        if not nome:
            disponiveis = ", ".join(telemetria.cenarios_disponiveis())
            return f"Informe um cenário. Disponíveis: {disponiveis}"
        aplicado = telemetria.set_cenario(nome)
        if aplicado:
            return f"✓ Cenário '{aplicado}' ativado. A próxima leitura refletirá essa condição."
        disponiveis = ", ".join(telemetria.cenarios_disponiveis())
        return f"✗ Cenário '{nome}' inválido. Disponíveis: {disponiveis}"

    def _coletar_estado(self):
        """Coleta telemetria, avalia alertas e atualiza a memória."""
        dados = telemetria.coletar()
        diagnostico = alertas.avaliar(dados)
        self.historico.append((dados, diagnostico))
        return dados, diagnostico

    def _resumo_historico(self):
        """Resumo curto dos ciclos anteriores para dar contexto temporal à IA."""
        if len(self.historico) <= 1:
            return "Sem ciclos anteriores registrados (início da sessão)."
        linhas = []
        for dados, diag in list(self.historico)[:-1]:
            linhas.append(f"  - Ciclo #{dados['ciclo']}: nível {diag['nivel_geral'].upper()}")
        return "\n".join(linhas)

    def status_snapshot(self):
        """Retorna texto resumindo o estado atual da telemetria + alertas."""
        dados, diagnostico = self._coletar_estado()
        return (
            telemetria.formatar_legivel(dados)
            + "\n\n"
            + alertas.formatar_legivel(diagnostico)
        )

    def analyze(self, pergunta_usuario):
        """Analisa a pergunta com base na telemetria + alertas + IA.

        Fluxo:
          1. Coleta dados via telemetria.coletar()
          2. Avalia alertas via alertas.avaliar(dados)  (decisão em Python)
          3. Monta prompt com dados + alertas + ações + histórico + pergunta
          4. Chama llm(prompt, system=self.system_prompt)
          5. Retorna a resposta da IA (com cabeçalho de telemetria)
        """
        dados, diagnostico = self._coletar_estado()

        telemetria_txt = telemetria.formatar_legivel(dados)
        diagnostico_txt = alertas.formatar_legivel(diagnostico)
        historico_txt = self._resumo_historico()

        prompt = f"""DADOS DE TELEMETRIA ATUAIS DO SATÉLITE GNSS
{telemetria_txt}

DIAGNÓSTICO AUTOMÁTICO (calculado em Python, não invente outro)
{diagnostico_txt}

HISTÓRICO DOS CICLOS ANTERIORES
{historico_txt}

PERGUNTA DO OPERADOR
{pergunta_usuario}

Responda seguindo rigorosamente o formato e as regras do seu papel.
Use SOMENTE os valores de telemetria e o diagnóstico fornecidos acima —
não invente parâmetros nem reclassifique severidades."""

        resposta_ia = llm(prompt, system=self.system_prompt)

        cabecalho = f"[ciclo #{dados['ciclo']} · nível {diagnostico['nivel_geral'].upper()}]\n\n"
        return cabecalho + resposta_ia
