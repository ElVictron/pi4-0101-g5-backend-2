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

Cada mensagem é um objeto JSON com o campo `evento` igual a
`bibliotecaAtualizada` e os campos da tabela no mesmo nível. Exemplo:

```json
{
  "evento": "bibliotecaAtualizada",
  "tipo": "emprestimo_registrado",
  "livroId": 101,
  "emprestimoId": 9001,
  "status": "ativo",
  "quantidadeDisponivel": 2,
  "atualizadaEm": "2026-10-13T19:20:00"
}
```

Quando o CT12 não traz `emprestimoId` ou envia `null`, a mensagem omite
esse campo. O Backend 2 só repassa os campos do CT13.

## Ordem das mensagens

O Backend 2 repassa as mensagens na ordem em que aceita as publicações, mas essa ordem pode diferir da ordem dos fatos: um reenvio do Backend 1 (CT12) pode trazer um evento antigo depois de um novo. Por isso o Frontend guarda, por livro, o `atualizadaEm` da última mensagem aplicada e ignora mensagens com `atualizadaEm` anterior. Mensagens com o mesmo `atualizadaEm` são aplicadas na ordem de chegada. O formato `AAAA-MM-DDTHH:MM:SS` permite comparar os textos diretamente.

## Saída

não tem.

## Erros

| Quando | O que volta |
|---|---|
| Painel estava fechado durante o envio | Nada. Ao abrir, o Frontend busca os dados pelas operações CT7 e CT8 |
| Conexão WSS perdida | O Frontend tenta reconectar; até reconectar, a atualização é recuperada por nova consulta HTTPS |
| Painel deixa de acompanhar as atualizações | Se a fila de 32 eventos lotar, o painel é desconectado com código WebSocket 1013 e segue o mesmo fluxo de recuperação |
