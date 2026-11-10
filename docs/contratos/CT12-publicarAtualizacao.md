# CT12: publicarAtualizacao

| Linha | Valor |
|---|---|
| Fronteira | HTTPS |
| Quem chama | Backend 1 |
| Quem responde | Backend 2 |
| Atende | E5 e E6 |
| Como chamar | `POST /eventos/biblioteca` |

## Entrada

| Campo | Tipo | Obrigatório | Exemplo |
|---|---|---|---|
| tipo | um de: emprestimo_registrado, devolucao_registrada | sim | emprestimo_registrado |
| livroId | inteiro | sim | 101 |
| usuarioId | inteiro | não | 55 |
| emprestimoId | inteiro | não | 9001 |
| status | um de: ativo, devolvido, atrasado | sim | ativo |
| quantidadeDisponivel | inteiro | sim | 2 |
| atualizadaEm | data e hora | sim | 2026-10-13T19:20:00 |

O corpo é um objeto JSON UTF-8 de até 64 KiB. IDs são inteiros positivos e `quantidadeDisponivel` é
um inteiro maior ou igual a zero. A data segue `AAAA-MM-DDTHH:MM:SS` no horário
de São Paulo, conforme o publicador do Backend 1. IDs opcionais podem estar
ausentes ou ter valor `null`. Campos desconhecidos são ignorados.

## Saída

| Campo | Tipo | Obrigatório | Exemplo |
|---|---|---|---|
| aceito | booleano | sim | true |
| eventoId | texto | sim | evt_9001 |

O Backend 2 responde com HTTP 200 e gera um identificador por publicação aceita,
inclusive quando nenhum painel está conectado.

## Erros

| Quando | O que volta |
|---|---|
| Tipo de evento inválido | Erro `EVENTO_INVALIDO` |
| Backend 2 indisponível | Erro `EVENTO_NAO_PUBLICADO`; o Backend 1 registra a falha para retry manual |
| Campo obrigatório ausente | Erro `CAMPOS_OBRIGATORIOS` |

Campos obrigatórios ausentes, nulos ou em branco recebem HTTP 400 com
`CAMPOS_OBRIGATORIOS`. Corpo JSON inválido e valores fora do contrato recebem
HTTP 400 com `EVENTO_INVALIDO`. O erro segue o formato
`{"erro":{"codigo":"EVENTO_INVALIDO","mensagem":"Evento inválido."}}`.

`EVENTO_NAO_PUBLICADO` descreve uma falha percebida pelo Backend 1. Em caso de
indisponibilidade, ele guarda o evento para reenvio, conforme os cards #793 e #798.
