"""Testes do contador (cocotb)."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, ReadOnly

from modelos import ler

LARGURA = 4
MAXIMO = 2**LARGURA - 1


async def iniciar(dut):
    Clock(dut.clk, 10, unit="ns").start()
    dut.rst.value = 1
    dut.habilita.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0


@cocotb.test()
async def reset_zera_o_contador(dut):
    await iniciar(dut)
    await ReadOnly()
    assert ler(dut.valor) == 0


@cocotb.test()
async def conta_um_por_ciclo_quando_habilitado(dut):
    await iniciar(dut)
    dut.habilita.value = 1
    for esperado in range(1, 6):
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert ler(dut.valor) == esperado


@cocotb.test()
async def sem_habilita_o_valor_nao_muda(dut):
    await iniciar(dut)
    dut.habilita.value = 1
    await ClockCycles(dut.clk, 3)
    dut.habilita.value = 0
    await ClockCycles(dut.clk, 10)
    await ReadOnly()
    assert ler(dut.valor) == 3


@cocotb.test()
async def volta_para_zero_depois_do_maximo(dut):
    await iniciar(dut)
    dut.habilita.value = 1
    await ClockCycles(dut.clk, MAXIMO)
    await ReadOnly()
    assert ler(dut.valor) == MAXIMO
    assert ler(dut.estouro) == 1, "estouro deve valer 1 no valor máximo com habilita"
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert ler(dut.valor) == 0
    assert ler(dut.estouro) == 0


@cocotb.test()
async def estouro_so_com_habilita(dut):
    await iniciar(dut)
    dut.habilita.value = 1
    await ClockCycles(dut.clk, MAXIMO)
    dut.habilita.value = 0
    await ReadOnly()
    assert ler(dut.valor) == MAXIMO
    assert ler(dut.estouro) == 0


@cocotb.test()
async def reset_no_meio_da_contagem(dut):
    await iniciar(dut)
    dut.habilita.value = 1
    await ClockCycles(dut.clk, 7)
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert ler(dut.valor) == 0, "reset tem prioridade sobre habilita"
