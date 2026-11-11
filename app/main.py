import json
from asyncio import Queue, QueueFull
from contextlib import suppress
from datetime import datetime
from typing import Annotated, Literal
from uuid import uuid4

from anyio import CancelScope, create_task_group
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

Id = Annotated[int, Field(gt=0)]
MAX_CORPO_BYTES = 64 * 1024
MAX_EVENTOS_POR_PAINEL = 32


class EventoBiblioteca(BaseModel):
    model_config = ConfigDict(strict=True)

    tipo: Literal["emprestimo_registrado", "devolucao_registrada"]
    livroId: Id
    usuarioId: Id | None = None
    emprestimoId: Id | None = None
    status: Literal["ativo", "devolvido", "atrasado"]
    quantidadeDisponivel: Annotated[int, Field(ge=0)]
    atualizadaEm: Annotated[
        str, Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$")
    ]

    @field_validator("atualizadaEm")
    @classmethod
    def conferir_data(cls, valor: str) -> str:
        datetime.fromisoformat(valor)
        return valor


CAMPOS_OBRIGATORIOS = tuple(
    nome for nome, campo in EventoBiblioteca.model_fields.items() if campo.is_required()
)


def erro(codigo: str, mensagem: str) -> JSONResponse:
    return JSONResponse({"erro": {"codigo": codigo, "mensagem": mensagem}}, status_code=400)


async def ler_objeto_json(request: Request) -> dict:
    corpo = bytearray()
    async for parte in request.stream():
        if len(corpo) + len(parte) > MAX_CORPO_BYTES:
            raise ValueError("Corpo acima de 64 KiB.")
        corpo.extend(parte)
    dados = json.loads(corpo.decode("utf-8"))
    if not isinstance(dados, dict):
        raise ValueError("O corpo precisa ser um objeto JSON.")
    return dados


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    paineis: dict[WebSocket, tuple[Queue[dict], CancelScope]] = {}

    @app.get("/saude")
    async def saude() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/eventos/biblioteca", response_model=None)
    async def publicarAtualizacao(request: Request) -> dict | JSONResponse:
        try:
            dados = await ler_objeto_json(request)
        except (ValueError, RecursionError):
            return erro("EVENTO_INVALIDO", "Envie um objeto JSON válido de até 64 KiB.")

        faltantes = [
            nome
            for nome in CAMPOS_OBRIGATORIOS
            if dados.get(nome) is None or (isinstance(dados[nome], str) and not dados[nome].strip())
        ]
        if faltantes:
            return erro("CAMPOS_OBRIGATORIOS", f"Preencha: {', '.join(faltantes)}.")
        try:
            evento = EventoBiblioteca.model_validate(dados)
        except ValidationError:
            return erro("EVENTO_INVALIDO", "Evento fora do contrato CT12.")

        mensagem = {"evento": "bibliotecaAtualizada"} | evento.model_dump(
            exclude={"usuarioId"}, exclude_none=True
        )
        # Cada fila tem um único emissor, preservando a ordem e isolando painéis lentos.
        for conexao, (fila, escopo) in tuple(paineis.items()):
            try:
                fila.put_nowait(mensagem)
            except QueueFull:
                del paineis[conexao]
                escopo.cancel()
        return {"aceito": True, "eventoId": f"evt_{uuid4().hex}"}

    @app.websocket("/ws/biblioteca")
    async def biblioteca(conexao: WebSocket) -> None:
        fila: Queue[dict] = Queue(maxsize=MAX_EVENTOS_POR_PAINEL)

        async with create_task_group() as tarefas:

            async def enviar() -> None:
                try:
                    while True:
                        await conexao.send_json(await fila.get())
                except (WebSocketDisconnect, OSError):
                    tarefas.cancel_scope.cancel()

            await conexao.accept()
            paineis[conexao] = (fila, tarefas.cancel_scope)
            tarefas.start_soon(enviar)
            try:
                while (await conexao.receive())["type"] != "websocket.disconnect":
                    pass
            finally:
                painel_lento = paineis.pop(conexao, None) is None
                tarefas.cancel_scope.cancel()

        if painel_lento:
            with suppress(WebSocketDisconnect, OSError):
                await conexao.close(code=1013)

    return app
