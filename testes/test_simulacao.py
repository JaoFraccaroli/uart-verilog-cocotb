"""
Liga o Pytest aos testes cocotb: para cada circuito, compila o Verilog com
o Icarus Verilog e roda os testes em Python contra a simulação.

Rodar:  pytest
"""
from pathlib import Path

import pytest
from cocotb_tools.runner import get_runner

RAIZ = Path(__file__).resolve().parent.parent
RTL = RAIZ / "rtl"
TESTES = Path(__file__).resolve().parent


def simular(topo: str, fontes: list[str], modulo_de_teste: str, parametros: dict | None = None):
    parametros = parametros or {}
    sufixo = "_".join(f"{k}{v}" for k, v in parametros.items()) or "padrao"
    pasta = RAIZ / "sim_build" / f"{topo}_{sufixo}"
    runner = get_runner("icarus")
    runner.build(
        sources=[RTL / f for f in fontes],
        hdl_toplevel=topo,
        parameters=parametros,
        build_dir=pasta,
        timescale=("1ns", "1ps"),
        waves=True,
        always=True,
    )
    runner.test(
        hdl_toplevel=topo,
        test_module=modulo_de_teste,
        test_dir=TESTES,
        build_dir=pasta,
        extra_env={k: str(v) for k, v in parametros.items()},
        results_xml=str(pasta / "resultados.xml"),
        waves=True,
    )


def test_contador():
    simular("contador", ["contador.v"], "tb_contador", {"LARGURA": 4})


@pytest.mark.parametrize("clks_por_bit", [4, 8, 33])
def test_uart_tx(clks_por_bit):
    simular("uart_tx", ["uart_tx.v"], "tb_uart_tx", {"CLKS_POR_BIT": clks_por_bit})


@pytest.mark.parametrize("clks_por_bit", [4, 8, 32])
def test_uart_rx(clks_por_bit):
    simular("uart_rx", ["uart_rx.v"], "tb_uart_rx", {"CLKS_POR_BIT": clks_por_bit})


@pytest.mark.parametrize("clks_por_bit", [8, 32])
def test_eco_uart(clks_por_bit):
    simular("eco_uart", ["uart_rx.v", "uart_tx.v", "eco_uart.v"], "tb_eco_uart", {"CLKS_POR_BIT": clks_por_bit})
