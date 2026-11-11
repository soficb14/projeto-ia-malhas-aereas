"""Testes do agente Qwen sem baixar o modelo: a geração é simulada com textos
no formato que o Qwen2.5 produz (<tool_call>{...}</tool_call>)."""
import json

from src.agent.agent_qwen import QwenAgent, extrair_chamadas, normalizar_args
from src.agent.fabrica import criar_agente
from src.agent.tools import FlightTools
from test_tools import FakeBackend   # pytest põe a pasta tests/ no sys.path


def _agente(saidas):
    """QwenAgent cujo modelo devolve, em ordem, os textos de `saidas`."""
    agente = QwenAgent(FlightTools(FakeBackend()), prompt_version="v1")
    fila = list(saidas)
    agente.vistas = []

    def falso(messages):
        agente.vistas.append(json.loads(json.dumps(messages)))
        return fila.pop(0), 100, 20

    agente._gerar = falso
    return agente


def _call(**args):
    return "<tool_call>\n" + json.dumps({"name": "buscar_rota", "arguments": args}) + "\n</tool_call>"


def test_extrai_chamada_valida():
    antes, c = extrair_chamadas('Vou buscar.\n' + _call(origem="CLT", destino="LAX"))
    assert antes == "Vou buscar."
    assert c == [{"nome": "buscar_rota", "args": {"origem": "CLT", "destino": "LAX"}}]


def test_extrai_chamada_sem_tag_de_fechamento_e_args_em_texto():
    texto = '<tool_call>{"name": "buscar_rota", "arguments": "{\\"origem\\": \\"CLT\\", \\"destino\\": \\"ATL\\"}"}'
    _, c = extrair_chamadas(texto)
    assert c[0]["args"] == {"origem": "CLT", "destino": "ATL"}


def test_json_quebrado_vira_invalida():
    _, c = extrair_chamadas("<tool_call>{nome: buscar_rota</tool_call>")
    assert "invalida" in c[0]


def test_sem_chamada_e_resposta_direta():
    antes, c = extrair_chamadas("Só planejo rotas aéreas.")
    assert c == [] and antes == "Só planejo rotas aéreas."


def test_normaliza_tipos():
    a = normalizar_args({"origem": "CLT", "destino": "LAX", "evitar": "ATL, DFW",
                         "vento": "-10", "congestionamento": "3", "clima": None,
                         "eventos": {"de": "CLT", "para": "ATL", "tipo": "Storm"}})
    assert a["evitar"] == ["ATL", "DFW"] and a["vento"] == -10.0
    assert a["congestionamento"] == 3 and "clima" not in a
    assert a["eventos"] == [{"de": "CLT", "para": "ATL", "tipo": "Storm"}]


def test_ciclo_completo_ferramenta_e_resposta():
    ag = _agente([_call(origem="CLT", destino="LAX"), "A rota é CLT -> LAX."])
    r = ag.run("Rota de CLT para LAX")
    assert r["erro"] is None and r["resposta"] == "A rota é CLT -> LAX."
    assert r["chamadas"][0]["nome"] == "buscar_rota"
    assert r["chamadas"][0]["saida"]["ok"] is True
    assert r["tokens_in"] == 200 and r["tokens_out"] == 40
    # a segunda chamada ao modelo recebeu a chamada (args como dict) e o resultado da ferramenta
    msgs = ag.vistas[1]
    assert msgs[-2]["tool_calls"][0]["function"]["arguments"] == {"origem": "CLT", "destino": "LAX"}
    assert msgs[-1]["role"] == "tool" and json.loads(msgs[-1]["content"])["ok"] is True


def test_codigo_inexistente_volta_para_o_modelo_explicar():
    ag = _agente([_call(origem="CLT", destino="XXX"), "XXX não existe na malha."])
    r = ag.run("CLT para XXX")
    assert r["chamadas"][0]["saida"]["ok"] is False and r["erro"] is None


def test_json_quebrado_da_uma_segunda_chance():
    ag = _agente(["<tool_call>{quebrado</tool_call>", _call(origem="CLT", destino="ATL"),
                  "CLT -> ATL"])
    r = ag.run("CLT para ATL")
    assert r["erro"] is None and r["chamadas"][-1]["saida"]["ok"] is True


def test_limite_de_turnos():
    ag = _agente([_call(origem="CLT", destino="ATL")] * 10)
    r = ag.run("CLT para ATL")
    assert r["erro"] and "Limite" in r["erro"]


def test_erro_do_modelo_nao_derruba():
    ag = QwenAgent(FlightTools(FakeBackend()))
    ag._gerar = lambda m: (_ for _ in ()).throw(RuntimeError("sem memória"))
    r = ag.run("CLT para ATL")
    assert "sem memória" in r["erro"] and r["resposta"] == ""


def test_fabrica():
    t = FlightTools(FakeBackend())
    assert isinstance(criar_agente(t, "qwen"), QwenAgent)
    try:
        criar_agente(t, "outro")
    except ValueError:
        pass
    else:
        raise AssertionError("deveria recusar backend desconhecido")
