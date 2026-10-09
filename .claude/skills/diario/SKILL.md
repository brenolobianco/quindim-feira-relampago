---
name: diario
description: Ajuda o Breno a escrever a entrada do dia no Diário do NOTAS.md, com as palavras dele.
disable-model-invocation: true
---

# Diário do dia

O §7.4 pede um diário curto, escrito pelo Breno. Meu papel é puxar a memória e organizar, não escrever por ele.

1. Rode `git log --since=midnight --format="%h %s"` e mostre em poucas linhas o que entrou hoje, para refrescar a memória.
2. Faça estas perguntas de uma vez, curtas:
   - O que você estudou hoje?
   - Onde travou, e como destravou (ou não)?
   - O que descobriu que não sabia?
   - Onde a IA ajudou, e onde ela errou ou te levou para o caminho errado?
   - Tomou alguma decisão ou achou alguma ambiguidade na especificação que deve ir para "Decisões"?
3. Espere as respostas. Se eu me lembrar de algo desta conversa em que a IA errou, posso lembrar o Breno, mas é ele quem decide se entra.
4. Monte a entrada com o **texto do Breno**: só organize em tópicos e corrija erros de digitação. Não acrescente conteúdo, não enfeite, não deixe com cara de texto gerado. Poucas linhas, no formato:

   ```
   ### DD/MM — dia N
   - ...
   ```

5. Mostre a entrada antes de salvar. Com o OK, salve em `NOTAS.md` sob `## Diário` (crie o arquivo com as seções `## Decisões` e `## Diário` se não existir). Decisões vão para `## Decisões`, também nas palavras dele.
6. Lembre: commit e push hoje.
