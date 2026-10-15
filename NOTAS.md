# Notas

## Decisões

**Concorrência sem transação.** O `mongo:8` em instância única não tem replica set, então não tem transação multi-documento. Cada SKU é separado com um `find_one_and_update` condicional (`disponivel >= quantidade` + `$inc`). Se um SKU da reserva falha, devolvo o que já tinha separado (compensação) e respondo 409 com todos os SKUs sem estoque. Nada fica em memória, porque são 4 workers do gunicorn.

**Expiração preguiçosa.** Não uso índice TTL nem rotina periódica (o TTL do Mongo roda a cada ~60s). Antes de cada requisição das rotas de catálogo, reserva e pedido, as reservas vencidas passam de `ativa` para `expirada` com `find_one_and_update`. Só quem fez a transição devolve as unidades, então cada unidade volta uma vez só.

**Confirmação idempotente.** A transição `ativa → confirmada` só acontece com `expira_em > agora`. O pedido é criado com upsert + `$setOnInsert` e índice único em `pedidos.reserva_id`, então confirmações simultâneas geram um pedido só. 201 para quem fez a transição, 200 para as repetições.

**Desconto e rateio.** Tudo em centavos inteiros. Arredondamento comercial com `(valor * pct + 50) // 100`, sem `float` nem `round()` (que arredonda meio para o par). O rateio usa `divmod` para a parte inteira e distribui a sobra pelo maior resto; o `sorted` é estável, então no empate ganha a primeira linha.

**Webhook.** HMAC-SHA256 sobre o corpo bruto (`request.get_data()`), comparado com `hmac.compare_digest`. Sem `WEBHOOK_SEGREDO` configurado, toda assinatura é recusada. O evento é gravado com `_id = evento_id`, então um evento repetido dá chave duplicada e não é aplicado. As transições só acontecem a partir de `aguardando_pagamento`, o que deixa `pago` e `cancelado` finais. Na recusa, só quem fez a transição devolve as unidades.

**Ambiguidades da especificação e o que escolhi:**

- SKU fora do catálogo na reserva: 400 (`requisicao_invalida`), não 404 nem 409. É um corpo fora do contrato.
- SKU repetido na mesma reserva: 400. Somar as quantidades poderia passar do limite de 3 por SKU sem ficar claro para o cliente.
- `estoque` nunca muda; só `disponivel` sobe e desce. Pedido pago continua segurando as unidades.
- O exemplo do §5.3 mostra `expira_em` 10 minutos depois de `criado_em`, mas a RN-03 diz 15 minutos (900 s). Segui a regra: `RESERVA_TTL_SEGUNDOS=900`.
- No trecho "Se o prazo apertar", o texto cita "dia 29", mas o prazo da avaliação é 15/10. Segui o 15/10.
- Evento com `pedido_id` malformado responde 200, como pedido inexistente, porque para o provedor qualquer outra resposta significa "tente de novo".

**Limitações conhecidas:**

- Se o processo cair entre gravar o evento do webhook e aplicá-lo, a reenviada do provedor é vista como duplicada e o evento se perde (o pedido fica em `aguardando_pagamento`). A alternativa seria aplicar antes de gravar, já que as transições condicionais são idempotentes.
- Se o processo cair no meio de uma reserva, depois de separar alguns SKUs e antes da compensação, essas unidades ficam presas. Sem transação, não há como evitar sem um processo de reconciliação.
- O teste de concorrência da confirmação é probabilístico: sem o índice único ele às vezes passa, porque depende de as requisições realmente baterem ao mesmo tempo.
- A expiração preguiçosa só roda quando chega uma requisição. Sem tráfego, a reserva continua `ativa` no banco depois do prazo (mas não pode mais ser confirmada).
- O frontend roda fora do `docker compose`, com `npm run dev`. Sem Docker na máquina eu não tinha como testar um Dockerfile dele, e um erro no build derrubaria o compose inteiro, inclusive a API.
- Não consegui validar o `docker compose up --build` a partir de um clone novo, porque a máquina em que desenvolvi não tinha Docker. Rodei a API e os testes com um `mongod` local.

## Diário

### 08/10 — dia 1
- Máquina sem Docker nem Python: instalei o uv e rodei um mongod portátil.
- App Flask com Mongo, erro padrão, catálogo com seed, reset do admin, validação da reserva com Pydantic e reserva com baixa atômica.
- Descobri que o `find_one_and_update` com filtro (`disponivel >= qtd`) checa e baixa o estoque numa operação só, sem brecha para duas pessoas levarem a última unidade.

### 09/10 — dia 2
- Teste da RN-04 com processos concorrentes de verdade, consulta de reserva e expiração preguiçosa.
- Descobri que o índice TTL do Mongo só apaga a cada ~60 s, então não serve para expirar a reserva na hora.

### 13/10 — dia 3
- Desconto da RN-07, rateio da RN-08 e confirmação gerando um único pedido.

### 14/10 — dia 4
- Teste de concorrência da confirmação e consulta de pedido.

### 15/10 — dia 5
- Webhook de pagamento, README e NOTAS. Tela em Nuxt no fim, fora do compose.
