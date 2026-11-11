import json
import socket
import ssl
from threading import Thread
from time import monotonic, sleep

import httpx
import pytest
import trustme
import uvicorn
from websockets.sync.client import connect

from app.main import create_app


@pytest.fixture
def servidor_tls(tmp_path):
    ca = trustme.CA()
    certificado = ca.issue_cert("127.0.0.1")
    caminho_cert = tmp_path / "cert.pem"
    caminho_chave = tmp_path / "key.pem"
    certificado.cert_chain_pems[0].write_to_path(caminho_cert)
    certificado.private_key_pem.write_to_path(caminho_chave)
    contexto = ssl.create_default_context()
    ca.configure_trust(contexto)

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        porta = listener.getsockname()[1]
        servidor = uvicorn.Server(
            uvicorn.Config(
                create_app(),
                ssl_certfile=str(caminho_cert),
                ssl_keyfile=str(caminho_chave),
                ws="websockets-sansio",
                log_level="warning",
            )
        )
        thread = Thread(target=servidor.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            limite = monotonic() + 5
            while not servidor.started and thread.is_alive() and monotonic() < limite:
                sleep(0.01)
            assert servidor.started
            yield f"127.0.0.1:{porta}", contexto
        finally:
            servidor.should_exit = True
            thread.join(timeout=5)
            assert not thread.is_alive()


def test_https_dispara_wss_com_verificacao_tls(servidor_tls):
    endereco, contexto = servidor_tls
    evento = {
        "tipo": "devolucao_registrada",
        "livroId": 101,
        "emprestimoId": 9001,
        "usuarioId": 55,
        "status": "devolvido",
        "quantidadeDisponivel": 1,
        "atualizadaEm": "2026-10-13T19:20:00",
    }
    with (
        httpx.Client(verify=contexto, trust_env=False, timeout=3) as cliente,
        connect(f"wss://{endereco}/ws/biblioteca", ssl=contexto, proxy=None) as painel,
    ):
        saude = cliente.get(f"https://{endereco}/saude")
        assert saude.status_code == 200
        resposta = cliente.post(f"https://{endereco}/eventos/biblioteca", json=evento)
        assert resposta.status_code == 200
        assert resposta.json()["aceito"] is True
        mensagem = json.loads(painel.recv(timeout=3))
        assert mensagem == {"evento": "bibliotecaAtualizada"} | {
            k: v for k, v in evento.items() if k != "usuarioId"
        }

    with (
        httpx.Client(trust_env=False, timeout=3) as cliente,
        pytest.raises(httpx.ConnectError, match="CERTIFICATE_VERIFY_FAILED"),
    ):
        cliente.get(f"https://{endereco}/saude")
