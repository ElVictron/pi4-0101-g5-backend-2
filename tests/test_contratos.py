import pytest
from fastapi.testclient import TestClient

from app.main import create_app

POST = "/eventos/biblioteca"
WS = "/ws/biblioteca"
EMPRESTIMO = {
    "tipo": "emprestimo_registrado",
    "livroId": 101,
    "usuarioId": 55,
    "emprestimoId": 9001,
    "status": "ativo",
    "quantidadeDisponivel": 0,
    "atualizadaEm": "2026-10-13T19:20:00",
}
DEVOLUCAO = {
    **EMPRESTIMO,
    "tipo": "devolucao_registrada",
    "status": "devolvido",
    "quantidadeDisponivel": 1,
}


@pytest.fixture
def cliente():
    with TestClient(create_app()) as client:
        yield client


def mensagem_esperada(payload):
    return {"evento": "bibliotecaAtualizada"} | {
        chave: valor
        for chave, valor in payload.items()
        if chave != "usuarioId" and valor is not None
    }


@pytest.mark.parametrize("payload", [EMPRESTIMO, DEVOLUCAO, EMPRESTIMO | {"status": "atrasado"}])
def test_publica_em_todos_os_paineis(cliente, payload):
    # CT12 e CT13 · sucesso, distribuição a todos e exclusão de usuarioId.
    with cliente.websocket_connect(WS) as primeiro, cliente.websocket_connect(WS) as segundo:
        resposta = cliente.post(POST, json=payload | {"campoExtra": "ignorado"})
        assert resposta.status_code == 200
        assert resposta.json()["aceito"] is True
        assert resposta.json()["eventoId"]
        assert primeiro.receive_json() == mensagem_esperada(payload)
        assert segundo.receive_json() == mensagem_esperada(payload)


def test_reconexao_recebe_apenas_eventos_novos(cliente):
    # CT13 · painel fechado durante o envio e reconexão sem replay.
    with cliente.websocket_connect(WS):
        pass
    primeiro = cliente.post(POST, json=EMPRESTIMO)
    assert primeiro.status_code == 200
    with cliente.websocket_connect(WS) as painel:
        novo = {k: v for k, v in DEVOLUCAO.items() if k != "emprestimoId"}
        resposta = cliente.post(POST, json=novo | {"usuarioId": None})
        assert resposta.status_code == 200
        assert resposta.json()["eventoId"] != primeiro.json()["eventoId"]
        assert painel.receive_json() == mensagem_esperada(novo)


@pytest.mark.parametrize(
    "campo", ["tipo", "livroId", "status", "quantidadeDisponivel", "atualizadaEm"]
)
def test_rejeita_campo_ausente(cliente, campo):
    # CT12 · CAMPOS_OBRIGATORIOS.
    resposta = cliente.post(POST, json={k: v for k, v in EMPRESTIMO.items() if k != campo})
    assert resposta.status_code == 400
    assert resposta.json()["erro"]["codigo"] == "CAMPOS_OBRIGATORIOS"


@pytest.mark.parametrize("valor", [None, " "])
def test_rejeita_obrigatorio_nulo_ou_em_branco(cliente, valor):
    resposta = cliente.post(POST, json=EMPRESTIMO | {"tipo": valor})
    assert resposta.status_code == 400
    assert resposta.json()["erro"]["codigo"] == "CAMPOS_OBRIGATORIOS"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("tipo", "livro_cadastrado"),
        ("livroId", True),
        ("livroId", 0),
        ("usuarioId", "55"),
        ("emprestimoId", -1),
        ("status", "pendente"),
        ("quantidadeDisponivel", -1),
        ("quantidadeDisponivel", 1.0),
        ("atualizadaEm", "2026-02-30T19:20:00"),
        ("atualizadaEm", "2026-10-13"),
    ],
)
def test_rejeita_valor_invalido_sem_publicar(cliente, campo, valor):
    # CT12 · EVENTO_INVALIDO. CT13 · o próximo evento válido chega primeiro.
    with cliente.websocket_connect(WS) as painel:
        resposta = cliente.post(POST, json=EMPRESTIMO | {campo: valor})
        assert resposta.status_code == 400
        assert resposta.json()["erro"]["codigo"] == "EVENTO_INVALIDO"
        assert cliente.post(POST, json=DEVOLUCAO).status_code == 200
        assert painel.receive_json() == mensagem_esperada(DEVOLUCAO)


@pytest.mark.parametrize("corpo", [b"", b"{", b"[]", b"null"])
def test_rejeita_corpo_invalido(cliente, corpo):
    resposta = cliente.post(POST, content=corpo, headers={"Content-Type": "application/json"})
    assert resposta.status_code == 400
    assert resposta.json()["erro"]["codigo"] == "EVENTO_INVALIDO"
