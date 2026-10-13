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

## Saída

| Campo | Tipo | Obrigatório | Exemplo |
|---|---|---|---|
| aceito | booleano | sim | true |
| eventoId | texto | sim | evt_9001 |

## Erros

| Quando | O que volta |
|---|---|
| Tipo de evento inválido | Erro `EVENTO_INVALIDO` |
| Backend 2 indisponível | Erro `EVENTO_NAO_PUBLICADO`; o Backend 1 registra a falha para retry manual |
| Campo obrigatório ausente | Erro `CAMPOS_OBRIGATORIOS` |
