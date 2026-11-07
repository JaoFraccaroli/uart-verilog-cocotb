"""Teste do circuito completo da placa: eco serial + LEDs (cocotb)."""
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly

from modelos import enviar_serial, ler, receber_serial

CLKS = int(os.environ.get("CLKS_POR_BIT", "8"))


async def iniciar(dut):
    Clock(dut.clk, 10, unit="ns").start()
    dut.botao_reset_n.value = 0
    dut.uart_rx.value = 1
    await ClockCycles(dut.clk, 3)
    dut.botao_reset_n.value = 1
    await ClockCycles(dut.clk, 2)


async def ler_varios(dut, quantidade):
    return [(await receber_serial(dut.uart_tx, dut.clk, CLKS))[0] for _ in range(quantidade)]


@cocotb.test()
async def devolve_uma_mensagem_inteira_sem_perder_bytes(dut):
    await iniciar(dut)
    mensagem = list("Ola, FPGA!".encode())
    leitura = cocotb.start_soon(ler_varios(dut, len(mensagem)))
    await FallingEdge(dut.clk)
    for byte in mensagem:                # sem pausa entre os bytes
        await enviar_serial(dut.uart_rx, dut.clk, byte, CLKS)
    assert bytes(await leitura) == bytes(mensagem)


@cocotb.test()
async def leds_mostram_o_ultimo_byte(dut):
    await iniciar(dut)
    await FallingEdge(dut.clk)
    await enviar_serial(dut.uart_rx, dut.clk, 0b101101, CLKS)
    await ClockCycles(dut.clk, CLKS)
    await ReadOnly()
    # LEDs da Tang Nano 9K acendem em 0: o valor sai invertido
    assert ler(dut.leds_n) == (~0b101101) & 0b111111


@cocotb.test()
async def botao_de_reset_apaga_os_leds(dut):
    await iniciar(dut)
    await FallingEdge(dut.clk)
    await enviar_serial(dut.uart_rx, dut.clk, 0xFF, CLKS)
    await ClockCycles(dut.clk, CLKS)
    dut.botao_reset_n.value = 0
    await ClockCycles(dut.clk, 2)
    await ReadOnly()
    assert ler(dut.leds_n) == 0b111111
