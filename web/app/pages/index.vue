<script setup lang="ts">
type Livro = { sku: string, titulo: string, preco_centavos: number, disponivel: number }
type Reserva = { id: string, expira_em: string }
type Linha = {
  sku: string
  quantidade: number
  valor_centavos: number
  desconto_centavos: number
  liquido_centavos: number
}
type Pedido = {
  id: string
  status: string
  linhas: Linha[]
  subtotal_centavos: number
  desconto_centavos: number
  total_centavos: number
}
type ErroDaApi = { data?: { erro?: { mensagem?: string, detalhes?: { skus?: string[] } } } }

const { data: catalogo, refresh } = await useFetch<{ livros: Livro[] }>('/api/livros')
const quantidades = ref<Record<string, number | null>>({})
const reserva = ref<Reserva | null>(null)
const pedido = ref<Pedido | null>(null)
const erro = ref('')
const agora = ref<number | null>(null)

const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const emReais = (centavos: number) => moeda.format(centavos / 100)

const itensEscolhidos = computed(() =>
  Object.entries(quantidades.value)
    .filter(([, quantidade]) => (quantidade ?? 0) > 0)
    .map(([sku, quantidade]) => ({ sku, quantidade })),
)

const segundosRestantes = computed(() => {
  if (!reserva.value || agora.value === null) return 0
  return Math.max(0, Math.floor((Date.parse(reserva.value.expira_em) - agora.value) / 1000))
})

const tempoRestante = computed(() => {
  const minutos = String(Math.floor(segundosRestantes.value / 60)).padStart(2, '0')
  const segundos = String(segundosRestantes.value % 60).padStart(2, '0')
  return `${minutos}:${segundos}`
})

let relogio: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  agora.value = Date.now()
  relogio = setInterval(() => (agora.value = Date.now()), 1000)
})
onUnmounted(() => clearInterval(relogio))

function mensagemDe(falha: unknown): string {
  const corpo = (falha as ErroDaApi).data?.erro
  if (!corpo?.mensagem) return 'Não foi possível falar com a API. Tente de novo.'
  const skus = corpo.detalhes?.skus
  return skus ? `${corpo.mensagem} SKUs: ${skus.join(', ')}.` : corpo.mensagem
}

async function executar(acao: () => Promise<void>) {
  erro.value = ''
  try {
    await acao()
  }
  catch (falha) {
    erro.value = mensagemDe(falha)
  }
  await refresh()
}

function reservar() {
  return executar(async () => {
    pedido.value = null
    reserva.value = await $fetch<Reserva>('/api/reservas', {
      method: 'POST',
      body: { cliente_id: 'cli_web', itens: itensEscolhidos.value },
    })
    quantidades.value = {}
  })
}

function confirmar() {
  return executar(async () => {
    pedido.value = await $fetch<Pedido>(`/api/reservas/${reserva.value?.id}/confirmar`, {
      method: 'POST',
    })
    reserva.value = null
  })
}
</script>

<template>
  <UContainer class="py-8 space-y-6">
    <h1 class="text-2xl font-bold">
      Feira Relâmpago
    </h1>

    <UAlert v-if="erro" color="error" :title="erro" />

    <UCard>
      <table class="w-full">
        <thead>
          <tr>
            <th class="text-left">Livro</th>
            <th>Preço</th>
            <th>Disponível</th>
            <th>Quantidade</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="livro in catalogo?.livros" :key="livro.sku">
            <td>{{ livro.titulo }}</td>
            <td class="text-center">{{ emReais(livro.preco_centavos) }}</td>
            <td class="text-center">{{ livro.disponivel }}</td>
            <td class="text-center">
              <UInputNumber v-model="quantidades[livro.sku]" :min="0" :max="3" />
            </td>
          </tr>
        </tbody>
      </table>
      <template #footer>
        <UButton :disabled="!itensEscolhidos.length" @click="reservar">
          Reservar
        </UButton>
      </template>
    </UCard>

    <UCard v-if="reserva">
      <p v-if="segundosRestantes > 0">
        Reserva ativa. Tempo restante: <strong>{{ tempoRestante }}</strong>
      </p>
      <p v-else>
        O tempo da reserva acabou.
      </p>
      <template #footer>
        <UButton @click="confirmar">
          Confirmar
        </UButton>
      </template>
    </UCard>

    <UCard v-if="pedido">
      <template #header>
        Pedido {{ pedido.id }} ({{ pedido.status }})
      </template>
      <table class="w-full">
        <thead>
          <tr>
            <th class="text-left">SKU</th>
            <th>Qtd.</th>
            <th>Valor</th>
            <th>Desconto</th>
            <th>Líquido</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="linha in pedido.linhas" :key="linha.sku">
            <td>{{ linha.sku }}</td>
            <td class="text-center">{{ linha.quantidade }}</td>
            <td class="text-center">{{ emReais(linha.valor_centavos) }}</td>
            <td class="text-center">{{ emReais(linha.desconto_centavos) }}</td>
            <td class="text-center">{{ emReais(linha.liquido_centavos) }}</td>
          </tr>
        </tbody>
      </table>
      <template #footer>
        Subtotal {{ emReais(pedido.subtotal_centavos) }} · Desconto
        {{ emReais(pedido.desconto_centavos) }} · <strong>Total {{ emReais(pedido.total_centavos) }}</strong>
      </template>
    </UCard>
  </UContainer>
</template>
