"""Testes do modelo de referência (rodam sem simulador)."""
import pytest

from modelos import bits_para_byte, quadro_uart


@pytest.mark.parametrize("byte, quadro", [
    (0x00, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
    (0xFF, [0, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (0x01, [0, 1, 0, 0, 0, 0, 0, 0, 0, 1]),   # o bit menos significativo vai primeiro
    (0x80, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
    (0x41, [0, 1, 0, 0, 0, 0, 0, 1, 0, 1]),   # letra "A"
])
def test_quadro_uart(byte, quadro):
    assert quadro_uart(byte) == quadro


def test_quadro_tem_dez_bits():
    assert all(len(quadro_uart(b)) == 10 for b in range(256))


@pytest.mark.parametrize("byte", [-1, 256, 1000])
def test_byte_invalido(byte):
    with pytest.raises(ValueError):
        quadro_uart(byte)


def test_ida_e_volta_para_todos_os_bytes():
    for byte in range(256):
        assert bits_para_byte(quadro_uart(byte)[1:9]) == byte
