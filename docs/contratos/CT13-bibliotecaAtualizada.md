# CT13: bibliotecaAtualizada

| Linha | Valor |
|---|---|
| Fronteira | WSS |
| Quem chama | Backend 2, depois de aceitar CT12 |
| Quem responde | Frontend, em todos os painéis conectados. Não há resposta. |
| Atende | E5, E6 |
| Como chamar | Canal `wss://.../ws/biblioteca`, mensagem do tipo `bibliotecaAtualizada` |

## Entrada

| Campo | Tipo | Obrigatório | Exemplo |
|---|---|---|---|
| tipo | um de: emprestimo_registrado, devolucao_registrada | sim | emprestimo_registrado |
| livroId | inteiro | sim | 101 |
| emprestimoId | inteiro | não | 9001 |
| status | um de: ativo, devolvido, atrasado | sim | ativo |
| quantidadeDisponivel | inteiro | sim | 2 |
| atualizadaEm | data e hora | sim | 2026-10-13T19:20:00 |

## Saída

não tem.

## Erros

| Quando | O que volta |
|---|---|
| Painel estava fechado durante o envio | Nada. Ao abrir, o Frontend busca os dados pelas operações CT7 e CT8 |
| Conexão WSS perdida | O Frontend tenta reconectar; até reconectar, a atualização é recuperada por nova consulta HTTPS |
