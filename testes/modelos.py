"""
Modelo de referência da UART em Python.

Os testes comparam o circuito em Verilog com este modelo: ele faz o papel
do "outro lado do cabo", enviando e recebendo bits na mesma temporização
de uma UART de verdade.
"""
from cocotb.triggers import ClockCycles, RisingEdge

BITS_DE_DADOS = 8


def quadro_uart(byte: int) -> list[int]:
    """Bits de um quadro 8N1: início (0), dados do menos significativo
    para o mais significativo e parada (1)."""
    if not 0 <= byte <= 0xFF:
        raise ValueError(f"byte fora do intervalo 0..255: {byte}")
    return [0] + [(byte >> i) & 1 for i in range(BITS_DE_DADOS)] + [1]


def bits_para_byte(bits: list[int]) -> int:
    """Inverso de quadro_uart para os 8 bits de dados."""
    return sum(bit << i for i, bit in enumerate(bits))


def ler(sinal) -> int:
    return int(sinal.value)


async def enviar_serial(linha, clk, byte: int, clks_por_bit: int, bit_de_parada: int = 1) -> None:
    """Coloca um quadro UART na linha, bit a bit (como um computador faria)."""
    bits = quadro_uart(byte)
    bits[-1] = bit_de_parada
    for bit in bits:
        linha.value = bit
        await ClockCycles(clk, clks_por_bit)
    linha.value = 1


async def receber_serial(linha, clk, clks_por_bit: int, limite_ciclos: int = 100_000) -> tuple[int, int]:
    """Lê um quadro UART da linha, amostrando no meio de cada bit.
    Devolve (byte, bit de parada)."""
    for _ in range(limite_ciclos):
        await RisingEdge(clk)
        if ler(linha) == 0:
            break
    else:
        raise TimeoutError("nenhum bit de início na linha")

    await ClockCycles(clk, clks_por_bit // 2)
    assert ler(linha) == 0, "bit de início não se manteve em 0 até o meio do bit"

    bits = []
    for _ in range(BITS_DE_DADOS):
        await ClockCycles(clk, clks_por_bit)
        bits.append(ler(linha))
    await ClockCycles(clk, clks_por_bit)
    return bits_para_byte(bits), ler(linha)
