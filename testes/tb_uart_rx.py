"""Testes do receptor UART (cocotb)."""
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge

from modelos import enviar_serial, ler

CLKS = int(os.environ.get("CLKS_POR_BIT", "8"))
BYTES_DE_FRONTEIRA = [0x00, 0xFF, 0x01, 0x80, 0x55, 0xAA, 0x7F, 0xFE]


async def iniciar(dut):
    Clock(dut.clk, 10, unit="ns").start()
    dut.rst.value = 1
    dut.rx.value = 1
    await ClockCycles(dut.clk, 3)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)


async def capturar(dut, ciclos: int):
    """Observa as saídas por alguns ciclos e devolve o que aconteceu."""
    bytes_validos, erros, duracoes = [], 0, []
    pulso = 0
    for _ in range(ciclos):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if ler(dut.valido):
            if pulso == 0:
                bytes_validos.append(ler(dut.dado))
            pulso += 1
        elif pulso:
            duracoes.append(pulso)
            pulso = 0
        if ler(dut.erro_quadro):
            erros += 1
    if pulso:
        duracoes.append(pulso)
    return bytes_validos, erros, duracoes


async def receber(dut, bytes_enviados, clks_do_remetente=None, bit_de_parada=1):
    clks = clks_do_remetente or CLKS
    observacao = cocotb.start_soon(capturar(dut, (len(bytes_enviados) + 2) * 10 * max(clks, CLKS)))
    await FallingEdge(dut.clk)
    for byte in bytes_enviados:
        await enviar_serial(dut.rx, dut.clk, byte, clks, bit_de_parada)
    return await observacao


@cocotb.test()
async def bytes_de_fronteira(dut):
    await iniciar(dut)
    recebidos, erros, _ = await receber(dut, BYTES_DE_FRONTEIRA)
    assert recebidos == BYTES_DE_FRONTEIRA
    assert erros == 0


@cocotb.test()
async def todos_os_256_bytes_em_sequencia(dut):
    await iniciar(dut)
    recebidos, erros, _ = await receber(dut, list(range(256)))
    assert recebidos == list(range(256))
    assert erros == 0


@cocotb.test()
async def valido_dura_exatamente_um_ciclo(dut):
    await iniciar(dut)
    _, _, duracoes = await receber(dut, [0x42, 0x43])
    assert duracoes == [1, 1]


@cocotb.test()
async def bit_de_parada_errado_gera_erro_de_quadro(dut):
    await iniciar(dut)
    recebidos, erros, _ = await receber(dut, [0x5A], bit_de_parada=0)
    assert recebidos == [], "byte com quadro inválido não pode ser entregue"
    assert erros == 1


@cocotb.test()
async def ruido_curto_nao_vira_byte(dut):
    await iniciar(dut)
    observacao = cocotb.start_soon(capturar(dut, 20 * CLKS))
    await FallingEdge(dut.clk)
    dut.rx.value = 0                     # pulso menor que meio bit
    await ClockCycles(dut.clk, max(1, CLKS // 4))
    dut.rx.value = 1
    recebidos, erros, _ = await observacao
    assert recebidos == [] and erros == 0


@cocotb.test()
async def volta_a_funcionar_depois_de_um_erro(dut):
    await iniciar(dut)
    await receber(dut, [0x11], bit_de_parada=0)
    recebidos, erros, _ = await receber(dut, [0x22])
    assert recebidos == [0x22] and erros == 0


@cocotb.test(skip=CLKS < 32)
async def tolera_remetente_um_pouco_mais_lento_ou_rapido(dut):
    """Relógios de verdade nunca são idênticos. Com 32 ciclos por bit,
    um remetente com +-1 ciclo por bit (cerca de 3%) ainda é entendido."""
    await iniciar(dut)
    for clks_remetente in (CLKS - 1, CLKS + 1):
        recebidos, erros, _ = await receber(dut, [0x55, 0xA3, 0x00, 0xFF], clks_remetente)
        assert recebidos == [0x55, 0xA3, 0x00, 0xFF], f"falhou com {clks_remetente} ciclos por bit"
        assert erros == 0


@cocotb.test(skip=CLKS < 32)
async def diferenca_grande_de_velocidade_nao_passa_despercebida(dut):
    """Com diferença de cerca de 12% (4 ciclos em 32), o receptor não pode
    entregar os bytes como se estivesse tudo certo."""
    await iniciar(dut)
    enviados = [0x55, 0xA3, 0x0F, 0xF0]
    for clks_remetente in (CLKS - 4, CLKS + 4):
        recebidos, erros, _ = await receber(dut, enviados, clks_remetente)
        assert recebidos != enviados or erros > 0
