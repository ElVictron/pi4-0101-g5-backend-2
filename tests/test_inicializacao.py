import pytest

import app.__main__ as inicio
from app.main import create_app


@pytest.fixture
def uvicorn_registrado(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        inicio.uvicorn, "run", lambda *args, **kwargs: chamadas.append((args, kwargs))
    )
    return chamadas


@pytest.mark.parametrize("faltando", ["SSL_CERTFILE", "SSL_KEYFILE", "ambos"])
def test_exige_certificado_e_chave(monkeypatch, uvicorn_registrado, faltando):
    # CT12/CT13 · só HTTPS e WSS: sem os dois arquivos o processo não sobe.
    monkeypatch.setenv("SSL_CERTFILE", "cert.pem")
    monkeypatch.setenv("SSL_KEYFILE", "chave.pem")
    if faltando in ("SSL_CERTFILE", "ambos"):
        monkeypatch.delenv("SSL_CERTFILE")
    if faltando in ("SSL_KEYFILE", "ambos"):
        monkeypatch.delenv("SSL_KEYFILE")

    with pytest.raises(SystemExit) as erro:
        inicio.main()

    assert "SSL_CERTFILE" in str(erro.value)
    assert "SSL_KEYFILE" in str(erro.value)
    assert uvicorn_registrado == []


def test_exige_valor_nao_vazio(monkeypatch, uvicorn_registrado):
    monkeypatch.setenv("SSL_CERTFILE", "")
    monkeypatch.setenv("SSL_KEYFILE", "chave.pem")

    with pytest.raises(SystemExit):
        inicio.main()

    assert uvicorn_registrado == []


def test_sobe_com_tls_e_padroes(monkeypatch, uvicorn_registrado):
    monkeypatch.setenv("SSL_CERTFILE", "cert.pem")
    monkeypatch.setenv("SSL_KEYFILE", "chave.pem")
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORTA", raising=False)

    inicio.main()

    ((args, kwargs),) = uvicorn_registrado
    assert type(args[0]) is type(create_app())
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 8443
    assert kwargs["ssl_certfile"] == "cert.pem"
    assert kwargs["ssl_keyfile"] == "chave.pem"
    assert kwargs["ws"] == "websockets-sansio"


def test_endereco_e_porta_configuraveis(monkeypatch, uvicorn_registrado):
    monkeypatch.setenv("SSL_CERTFILE", "cert.pem")
    monkeypatch.setenv("SSL_KEYFILE", "chave.pem")
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORTA", "9443")

    inicio.main()

    ((_, kwargs),) = uvicorn_registrado
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 9443
