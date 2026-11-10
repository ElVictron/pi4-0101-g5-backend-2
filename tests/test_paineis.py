import pytest
from anyio import sleep_forever
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from app.main import MAX_CORPO_BYTES, MAX_EVENTOS_POR_PAINEL, create_app


def test_painel_lento_nao_atrasa_os_demais(monkeypatch):
    enviar = WebSocket.send_json

    async def enviar_ou_bloquear(conexao, dados):
        if conexao.query_params.get("lento") == "1":
            await sleep_forever()
        await enviar(conexao, dados)

    monkeypatch.setattr(WebSocket, "send_json", enviar_ou_bloquear)
    with (
        TestClient(create_app()) as cliente,
        cliente.websocket_connect("/ws/biblioteca?lento=1") as lento,
        cliente.websocket_connect("/ws/biblioteca") as painel,
    ):
        for quantidade in range(MAX_EVENTOS_POR_PAINEL + 2):
            resposta = cliente.post(
                "/eventos/biblioteca",
                json={
                    "tipo": "devolucao_registrada",
                    "livroId": 101,
                    "status": "devolvido",
                    "quantidadeDisponivel": quantidade,
                    "atualizadaEm": "2026-10-13T19:20:00",
                },
            )
            assert resposta.json()["aceito"] is True
            assert painel.receive_json()["quantidadeDisponivel"] == quantidade
        with pytest.raises(WebSocketDisconnect) as erro:
            lento.receive_json()
        assert erro.value.code == 1013


@pytest.mark.parametrize(
    "corpo",
    [b" " * (MAX_CORPO_BYTES + 1), b'{"valor":"\xff"}'],
    ids=["acima-do-limite", "utf8-invalido"],
)
def test_rejeita_corpo_fora_dos_limites(corpo):
    with TestClient(create_app()) as cliente:
        resposta = cliente.post(
            "/eventos/biblioteca",
            content=corpo,
            headers={"Content-Type": "application/json"},
        )
    assert resposta.status_code == 400
    assert resposta.json()["erro"]["codigo"] == "EVENTO_INVALIDO"
