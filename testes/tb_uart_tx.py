"""Testes do transmissor UART (cocotb)."""
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge

from modelos import ler, receber_serial

CLKS = int(os.environ.get("CLKS_POR_BIT", "8"))
BYTES_DE_FRONTEIRA = [0x00, 0xFF, 0x01, 0x80, 0x55, 0xAA, 0x7F, 0xFE]


async def iniciar(dut):
    Clock(dut.clk, 10, unit="ns").start()
    dut.rst.value = 1
    dut.enviar.value = 0
    dut.dado.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


async def pedir_envio(dut, byte):
    await FallingEdge(dut.clk)
    dut.dado.value = byte
    dut.enviar.value = 1
    await FallingEdge(dut.clk)
    dut.enviar.value = 0


async def transmitir_e_ler(dut, byte):
    leitura = cocotb.start_soon(receber_serial(dut.tx, dut.clk, CLKS))
    await pedir_envio(dut, byte)
    return await leitura


@cocotb.test()
async def linha_em_repouso_fica_em_1(dut):
    await iniciar(dut)
    for _ in range(20):
        await RisingEdge(dut.clk)
        assert ler(dut.tx) == 1
        assert ler(dut.ocupado) == 0


@cocotb.test()
async def bytes_de_fronteira(dut):
    await iniciar(dut)
    for byte in BYTES_DE_FRONTEIRA:
        recebido, parada = await transmitir_e_ler(dut, byte)
        assert recebido == byte, f"enviado {byte:#04x}, lido {recebido:#04x}"
        assert parada == 1, "bit de parada deve ser 1"
        await ClockCycles(dut.clk, CLKS)


@cocotb.test()
async def todos_os_256_bytes(dut):
    await iniciar(dut)
    for byte in range(256):
        recebido, parada = await transmitir_e_ler(dut, byte)
        assert (recebido, parada) == (byte, 1), f"falhou no byte {byte:#04x}"
        await ClockCycles(dut.clk, CLKS)


async def contar_ciclos_ocupado(dut):
    ciclos = 0
    while True:
        await RisingEdge(dut.clk)
        await ReadOnly()
        if ler(dut.ocupado):
            ciclos += 1
        elif ciclos:
            return ciclos


@cocotb.test()
async def quadro_dura_exatamente_10_bits(dut):
    await iniciar(dut)
    contagem = cocotb.start_soon(contar_ciclos_ocupado(dut))
    await pedir_envio(dut, 0xA5)
    assert await contagem == 10 * CLKS


@cocotb.test()
async def bit_menos_significativo_sai_primeiro(dut):
    await iniciar(dut)
    await pedir_envio(dut, 0x01)
    # Meio do primeiro bit de dados = início + 1,5 bit
    await ClockCycles(dut.clk, CLKS + CLKS // 2)
    assert ler(dut.tx) == 1
    await ClockCycles(dut.clk, CLKS)
    assert ler(dut.tx) == 0


@cocotb.test()
async def pedido_durante_envio_e_ignorado(dut):
    await iniciar(dut)
    leitura = cocotb.start_soon(receber_serial(dut.tx, dut.clk, CLKS))
    await pedir_envio(dut, 0x3C)
    await ClockCycles(dut.clk, 3 * CLKS)
    await pedir_envio(dut, 0xFF)     # chega no meio: não pode corromper o byte atual
    recebido, parada = await leitura
    assert (recebido, parada) == (0x3C, 1)


@cocotb.test()
async def dado_pode_mudar_durante_o_envio(dut):
    await iniciar(dut)
    leitura = cocotb.start_soon(receber_serial(dut.tx, dut.clk, CLKS))
    await pedir_envio(dut, 0x96)
    dut.dado.value = 0x00            # o transmissor guardou uma cópia
    recebido, _ = await leitura
    assert recebido == 0x96


@cocotb.test()
async def reset_no_meio_volta_para_repouso(dut):
    await iniciar(dut)
    await pedir_envio(dut, 0x00)
    await ClockCycles(dut.clk, 4 * CLKS)
    assert ler(dut.ocupado) == 1
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert ler(dut.tx) == 1
    assert ler(dut.ocupado) == 0
