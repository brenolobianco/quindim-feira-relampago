def percentual_de_desconto(unidades: int) -> int:
    if unidades >= 5:
        return 15
    if unidades >= 3:
        return 10
    return 0


def calcular_desconto(subtotal_centavos: int, unidades: int) -> int:
    percentual = percentual_de_desconto(unidades)
    return (subtotal_centavos * percentual + 50) // 100
