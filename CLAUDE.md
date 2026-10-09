# Quindim — Feira Relâmpago

Avaliação técnica do Breno para o Clube Quindim (vaga Full Stack, ênfase backend).
Especificação completa: `.claude/avaliacao.pdf` (fora do git). Em dúvida sobre contrato ou regra, leia o PDF — não confie na memória.

- Prazo: **quinta 15/10/2026, 9h (Brasília)**. Tag `entrega` no commit final da `main`.
- Terça 13/10: mandar o link do repo ao Daniel, do jeito que estiver.
- Dúvidas: daniel.sclearuc@quindim.com.br — perguntar conta a favor.

## Como trabalhar comigo (modo tutor)

O Breno está aprendendo Python, Flask e MongoDB nesta semana e vai alterar o código **ao vivo** na entrevista. Ele precisa entender cada linha.

- Antes de escrever código, explique em poucas linhas o conceito e por que essa abordagem. Quando for algo novo (pymongo, Flask, Pydantic, pytest, Nuxt), aponte a página da documentação oficial que vale ler.
- Trabalhe em passos pequenos, do tamanho de um commit. Ao fim de cada passo, diga "bom ponto para commit" e resuma o que mudou. **Não escreva a mensagem de commit** — o Breno escreve, com as palavras dele.
- Nos trechos centrais (concorrência, expiração, desconto/rateio, webhook), prefira guiar o Breno a escrever. Se eu escrever, explique linha por linha e confirme que ficou claro.
- Ambiguidade na especificação: não decida sozinho. Aponte, dê as opções com prós e contras e lembre de registrar a decisão em `NOTAS.md`.
- Nunca escreva o Diário do `NOTAS.md` por conta própria (use `/diario`).

## Git — eu nunca

Não rodo `git commit`, `push`, `tag`, `rebase`, `reset --hard`, `--amend` nem `--force` (bloqueado em `.claude/settings.json`). O histórico é parte da avaliação (§7.5): commits pequenos, em português, com testes junto do código que testam, push todo dia, sem reescrever nada.

## Stack (não trocar)

| Camada | Uso |
|---|---|
| Linguagem | Python 3.12, **síncrono** (sem `async`) |
| HTTP | Flask 3, gunicorn com 4 workers no Compose |
| Banco | MongoDB 8 com **pymongo puro** (sem ODM) |
| Validação | Pydantic 2 |
| Testes / lint | pytest / Ruff |
| Dependências | uv, com `uv.lock` versionado |
| Frontend | Nuxt 4, Vue 3 `<script setup lang="ts">`, Nuxt UI 4 |
| Ambiente | Docker Compose, imagem `mongo:8` em instância única padrão (sem init de cluster) |

## Regras de código

- Domínio em português do Brasil: `Reserva`, `confirmar_reserva`, `estoque_insuficiente`.
- Dinheiro: `int` em centavos no banco, na API e nos cálculos. Nada de `float` nem `round()` (que arredonda meio para o par). Arredondamento comercial com inteiros: `(valor * pct + 50) // 100`.
- Datas: `datetime` com timezone UTC, `MongoClient(..., tz_aware=True)`, saída ISO 8601 com `Z`.
- Simplicidade (§7.6): sem camadas, repositórios ou interfaces "para o futuro", sem dependência desnecessária. Se um recurso do MongoDB resolve, use-o.
- **Nunca comentar código.** O código se explica por nomes claros e funções curtas. Explicações vão na conversa; decisões, no `NOTAS.md`.
- Boas práticas: nomes descritivos, funções pequenas com uma responsabilidade, type hints, sem código morto nem duplicado, Ruff sem avisos e teste junto de cada regra de negócio.
- Erros sempre `{"erro": {"codigo", "mensagem", "detalhes"}}`. Nunca 500 com stack trace ou HTML. Id malformado → 404.
- Contrato da API à risca (§5): o avaliador roda testes automatizados contra caminhos, campos e códigos HTTP.

## Armadilhas já identificadas

1. `mongo:8` em instância única não tem replica set, logo **não tem transação multi-documento**. Concorrência via updates atômicos condicionais em um documento (filtro `disponivel >= qtd` + `$inc`), com compensação quando um SKU falha no meio de uma reserva tudo-ou-nada.
2. Expiração não pode depender de rotina periódica (índice TTL roda a cada ~60s). Liberação preguiçosa em cada requisição; a transição atômica `ativa → expirada` decide quem devolve as unidades, exatamente uma vez.
3. Confirmação idempotente: índice único em `pedidos.reserva_id`; transição `ativa → confirmada` condicionada a `expira_em > agora`.
4. Webhook: HMAC sobre o **corpo bruto** (`request.get_data()`), `hmac.compare_digest`, índice único em `evento_id`, transições atômicas do status do pedido. Vetor de teste no §5.6 do PDF.
5. 4 workers do gunicorn: nada de estado ou trava em memória.
6. Nuxt: o navegador só fala com `server/api` (URL da API em `runtimeConfig` privado). Cuidado com hydration mismatch no contador regressivo e no `Intl.NumberFormat`.

## Prioridade se o tempo apertar

(1) catálogo, reserva e confirmação corretos sob concorrência → (2) expiração → (3) desconto e rateio → (4) webhook → (5) frontend. Histórico do git e `NOTAS.md` entram sempre.

## Comandos

<!-- preencher quando o projeto existir: subir, testar, lint -->
