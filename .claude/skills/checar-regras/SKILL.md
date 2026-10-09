---
name: checar-regras
description: Confere o código contra as regras de negócio RN-01 a RN-10 e o contrato da API da avaliação Quindim. Use antes de cada push.
disable-model-invocation: true
---

# Checar regras

Revise o código atual contra o checklist abaixo. Em dúvida sobre o texto exato de uma regra, consulte `.claude/avaliacao.pdf`.

## Como reportar

- Uma linha por item: ✅ cumpre · ❌ viola · ⚠️ duvidoso · ➖ ainda não implementado.
- Para ❌ e ⚠️: arquivo:linha, o cenário concreto que quebra (ex.: "duas requisições simultâneas pelo último QND-005") e o conceito que o Breno deve estudar para corrigir.
- **Não corrija nada.** Só aponte. O Breno decide e corrige.
- Termine com os 3 problemas mais importantes, na ordem de prioridade do §8.

## Checklist

**Regras de negócio**
- RN-01 — Todo dinheiro é `int` em centavos. Nenhum `float`, `round()` ou divisão `/` em conta de dinheiro.
- RN-02 — Seed: QND-001 (3990, 10), QND-002 (2990, 10), QND-003 (1995, 10), QND-004 (8990, 3), QND-005 (12900, 1); campos `estoque` e `disponivel`.
- RN-03 — Reserva com 1+ SKUs, no máximo 3 por SKU, tudo ou nada (falhou um, `disponivel` de todos volta ao que era). TTL de `RESERVA_TTL_SEGUNDOS`, padrão 900.
- RN-04 — Sob concorrência com vários processos, `disponivel` nunca negativo e reservado + vendido ≤ estoque. Nenhuma trava em memória. Sem transação multi-documento (Mongo sem replica set).
- RN-05 — A partir de `expira_em`, a reserva está expirada: não confirma, e as unidades voltam na próxima requisição (`GET /v1/livros` ou nova reserva), sem depender de job ou TTL index. Cada unidade volta exatamente uma vez.
- RN-06 — Uma reserva gera no máximo um pedido, inclusive com confirmações simultâneas. 201 na que criou, 200 nas repetições, sempre o mesmo pedido.
- RN-07 — Desconto por unidades: 1–2 → 0%, 3–4 → 10%, 5+ → 15%, sobre o subtotal, meio centavo sobe.
- RN-08 — Rateio: parte inteira proporcional; sobras um a um para o maior resto; empate → linha que aparece primeiro. Soma das linhas = desconto total. Exemplo: 3990/2990/1995 → 399/299/200 (total 898).
- RN-09 — Status do pedido só muda por webhook. `pago`: aguardando → pago. `recusado`: aguardando → cancelado e devolve unidades uma única vez. `pago` e `cancelado` são finais. Mesmo `evento_id` nunca aplicado duas vezes.
- RN-10 — Datas gravadas em UTC e expostas como `2026-10-01T12:00:00Z`.

**Contrato da API (§5)**
- Erro: `{"erro": {"codigo", "mensagem", "detalhes"}}`. 400 `requisicao_invalida`, 401 `nao_autorizado`, 404 `nao_encontrado` (inclusive id malformado), 409 `estoque_insuficiente` com `detalhes.skus`, 410 `reserva_expirada`. Nenhum 500 com stack trace ou HTML.
- `GET /v1/livros` → `{"livros": [{sku, titulo, preco_centavos, estoque, disponivel}]}`.
- `POST /v1/reservas` → 201 `{id, cliente_id, status, itens[{sku, quantidade, preco_centavos}], criado_em, expira_em}`.
- `GET /v1/reservas/{id}` → mesmo formato, com o status verdadeiro no instante da consulta (`ativa`, `confirmada`, `expirada`).
- `POST /v1/reservas/{id}/confirmar` → `{id, reserva_id, cliente_id, status, linhas[{sku, quantidade, preco_centavos, valor_centavos, desconto_centavos, liquido_centavos}], subtotal_centavos, desconto_centavos, total_centavos, criado_em, pago_em}`.
- `GET /v1/pedidos/{id}` → mesmo formato.
- `POST /v1/webhooks/pagamento` → `X-Assinatura` = HMAC-SHA256 hex do corpo bruto com `WEBHOOK_SEGREDO`; inválida → 401 sem processar nada. Duplicado, sem efeito ou pedido inexistente → 200 `{"recebido": true}`. `pago_em` = `ocorrido_em` do evento `pago`.
- `POST /v1/admin/reset` com `X-Admin-Token` → apaga reservas, pedidos e eventos, restaura o seed, 204.
- `GET /healthz` → 200 `{"status": "ok"}` quando fala com o Mongo.

**Entrega**
- `docker compose up --build` a partir de `cp .env.example .env` sobe API :8000, front :3000 e Mongo com seed.
- `.env` fora do git; `.env.example` com valores que funcionam.
- Frontend: navegador só fala com `server/api`; SSR ligado sem aviso de hidratação; moeda em BRL a partir de centavos; contagem regressiva.
- Testes: unidade de desconto/rateio sem banco; teste de RN-04 com Mongo real e concorrência real.

## Ao final

Se as ferramentas existirem no projeto, rode e reporte o resultado: `uv run ruff check`, `uv run ruff format --check`, `uv run pytest`. Confira também se o `git status` mostra algum `.env` ou `avaliacao.pdf` a caminho do repositório.
