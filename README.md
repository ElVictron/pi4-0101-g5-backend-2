# Backend 2 da biblioteca

O Backend 1 publica um evento em `POST /eventos/biblioteca` por HTTPS. O
Backend 2 valida o [CT12](docs/contratos/CT12-publicarAtualizacao.md) e
distribui `bibliotecaAtualizada` pelo canal WSS `/ws/biblioteca`, conforme o
[CT13](docs/contratos/CT13-bibliotecaAtualizada.md). O evento avisa as telas
conectadas para atualizar os dados da biblioteca.

## Arquitetura e escopo

- **#779 ·** O [ADR 0004](https://github.com/ElVictron/pi4-0101-g5-backend-1/blob/main/docs/adr/0004-websocket-em-python.md)
  define Python e substitui a decisão sobre Java do ADR 0003. O serviço usa
  FastAPI e Uvicorn para servir HTTPS e WSS na mesma porta.
- **#782 ·** O serviço valida o evento, retorna `aceito` e `eventoId` e
  distribui a mensagem aos painéis conectados. O CT13 define os campos da
  mensagem e a recuperação de dados via CT7/CT8 após desconexão. As conexões
  ficam em memória, em um único processo.
- **#793 e #798 ·** O Backend 1 calcula o atraso quando o prazo vence sem
  devolução, aceita a devolução de um empréstimo ativo ou atrasado e publica
  `devolucao_registrada` com status `devolvido` após gravar. Se a publicação
  falhar, o Backend 1 guarda o evento para reenvio manual.
- **#780 ·** A imagem do Backend 2 recebe certificado e chave por volume.
  No Compose do grupo, monte-os como somente leitura e use um certificado
  cujo nome corresponda ao endereço chamado por cada cliente.

## Executar

Com Python 3.12 e [uv](https://docs.astral.sh/uv/), a partir da raiz:

```powershell
uv sync --locked --extra dev
$env:SSL_CERTFILE = "certs/backend2.pem"
$env:SSL_KEYFILE = "certs/backend2-key.pem"
uv run --locked python -m app
```

O processo exige os dois arquivos PEM. A porta padrão é `8443`, configurável
com `PORTA`. O endereço padrão local é `127.0.0.1`, configurável com `HOST`.
Use um certificado que inclua o endereço usado na URL e cuja CA seja confiável
para o cliente. `GET /saude` retorna `{"status":"ok"}`.

### Integração com o Compose

O trecho abaixo é o serviço a incorporar ao Compose do grupo. Use
`BACKEND2_URL=https://backend2:8443` no Backend 1, com a CA montada e indicada
em `BACKEND2_CA_BUNDLE`. Para o navegador, encaminhe `/ws/biblioteca` pelo
proxy do Frontend com suporte a WebSocket e certificado confiável.
Restrinja a publicação `POST /eventos/biblioteca` à rede interna dos serviços.

```yaml
services:
  backend2:
    build: ../pi4-0101-g5-backend-2
    environment:
      SSL_CERTFILE: /certs/backend2.pem
      SSL_KEYFILE: /certs/backend2-key.pem
    volumes:
      - ./certs:/certs:ro
```

O certificado interno precisa incluir `backend2` e a chave montada precisa
estar acessível ao usuário do contêiner (UID 10002).

## Testes

```powershell
uv run --locked --extra dev pytest --cov=app.main --cov-branch
uv run --locked --extra dev ruff check .
uv run --locked --extra dev ruff format --check .
```

A suíte verifica os erros do CT12, a entrega e a reconexão do CT13, e a
publicação por HTTPS seguida de recepção por WSS com verificação de certificado.
