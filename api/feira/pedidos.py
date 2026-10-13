def percentual_de_desconto(unidades: int) -> int:
    if unidades >= 5:
        return 15
    if unidades >= 3:
        return 10
    return 0


def calcular_desconto(subtotal_centavos: int, unidades: int) -> int:
    percentual = percentual_de_desconto(unidades)
    return (subtotal_centavos * percentual + 50) // 100


def ratear_desconto(valores_centavos: list[int], desconto_centavos: int) -> list[int]:
    subtotal = sum(valores_centavos)
    proporcoes = [divmod(desconto_centavos * valor, subtotal) for valor in valores_centavos]
    descontos = [parte_inteira for parte_inteira, _ in proporcoes]
    sobra = desconto_centavos - sum(descontos)
    linhas_por_maior_resto = sorted(
        range(len(proporcoes)), key=lambda linha: proporcoes[linha][1], reverse=True
    )
    for linha in linhas_por_maior_resto[:sobra]:
        descontos[linha] += 1
    return descontos
