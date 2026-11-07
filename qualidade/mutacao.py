"""
Teste de mutação no hardware (mesma ideia da aula 06 de Qualidade de Software).

Cada mutante é um erro proposital no Verilog, do tipo que acontece de
verdade em projeto de chips (trocar a ordem dos bits, errar um contador
por um ciclo, esquecer uma verificação...). Para cada mutante, os testes
rodam: se algum falhar, o mutante foi "morto".

Uso:  python qualidade/mutacao.py
"""
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MINIMO = 90.0


@dataclass
class Mutante:
    nome: str
    arquivo: str
    original: str
    mutado: str


MUTANTES = [
    Mutante("Contador conta de 2 em 2", "rtl/contador.v",
            "valor <= valor + 1'b1;", "valor <= valor + 2'd2;"),
    Mutante("Estouro sem depender de habilita", "rtl/contador.v",
            "assign estouro = habilita && (valor == {LARGURA{1'b1}});",
            "assign estouro = (valor == {LARGURA{1'b1}});"),
    Mutante("Habilita ignorado", "rtl/contador.v",
            "else if (habilita)", "else"),
    Mutante("TX: bit de início com 1 ciclo a menos", "rtl/uart_tx.v",
            "INICIO: begin\n                    if (ciclos == CLKS_POR_BIT - 1) begin",
            "INICIO: begin\n                    if (ciclos == CLKS_POR_BIT - 2) begin"),
    Mutante("TX: bit mais significativo primeiro", "rtl/uart_tx.v",
            "tx     <= buffer[0];", "tx     <= buffer[7];"),
    Mutante("TX: bit de parada em 0", "rtl/uart_tx.v",
            "tx     <= 1'b1;  // bit de parada", "tx     <= 1'b0;  // bit de parada"),
    Mutante("TX: não guarda cópia do dado", "rtl/uart_tx.v",
            "tx     <= buffer[indice + 1'b1];", "tx     <= dado[indice + 1'b1];"),
    Mutante("TX: ocupado só nos dados", "rtl/uart_tx.v",
            "assign ocupado = (estado != OCIOSO);", "assign ocupado = (estado == DADOS);"),
    Mutante("RX: não confirma o bit de início", "rtl/uart_rx.v",
            "estado <= (rx_sinc == 1'b0) ? DADOS : OCIOSO;", "estado <= DADOS;"),
    Mutante("RX: não verifica o bit de parada", "rtl/uart_rx.v",
            "if (rx_sinc == 1'b1) begin\n                            dado   <= buffer;",
            "if (1'b1) begin\n                            dado   <= buffer;"),
    Mutante("RX: amostra no começo do bit", "rtl/uart_rx.v",
            "localparam MEIO_DO_BIT = (CLKS_POR_BIT - 1) / 2;", "localparam MEIO_DO_BIT = 0;"),
    Mutante("RX: válido nunca é limpo", "rtl/uart_rx.v",
            "            valido      <= 1'b0;\n            erro_quadro <= 1'b0;\n            case",
            "            erro_quadro <= 1'b0;\n            case"),
    Mutante("Eco: sem buffer de 1 byte", "rtl/eco_uart.v",
            "end else if (tem_pendente && !tx_ocupado && !enviar) begin",
            "end else if (tem_pendente && !enviar) begin"),
    Mutante("Eco: LEDs sem inversão", "rtl/eco_uart.v",
            "assign leds_n = ~ultimo[5:0];", "assign leds_n = ultimo[5:0];"),
]


def testes_passam() -> bool:
    resultado = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"],
                               cwd=RAIZ, capture_output=True, text=True, env=os.environ.copy())
    return resultado.returncode == 0


def main() -> int:
    if not testes_passam():
        print("Os testes precisam passar no circuito original antes da mutação.")
        return 1
    resultados = []
    for m in MUTANTES:
        caminho = RAIZ / m.arquivo
        original = caminho.read_bytes()
        texto = original.decode("utf-8")
        if texto.count(m.original) != 1:
            print(f"[ERRO] trecho não encontrado (ou repetido) para '{m.nome}'")
            return 1
        try:
            caminho.write_bytes(texto.replace(m.original, m.mutado).encode("utf-8"))
            morto = not testes_passam()
        finally:
            caminho.write_bytes(original)
        resultados.append((m, morto))
        print(f"[{'MORTO     ' if morto else 'SOBREVIVEU'}] {m.nome}")

    mortos = sum(morto for _, morto in resultados)
    score = 100 * mortos / len(resultados)
    print(f"\nMutation score: {mortos}/{len(resultados)} = {score:.1f}% (mínimo: {MINIMO:.0f}%)")
    linhas = ["| Mutante | Arquivo | Resultado |", "|---|---|---|"]
    linhas += [f"| {m.nome} | `{m.arquivo}` | {'✅ morto' if morto else '❌ sobreviveu'} |" for m, morto in resultados]
    (RAIZ / "relatorios").mkdir(exist_ok=True)
    (RAIZ / "relatorios" / "mutacao.md").write_text(
        f"### Teste de mutação no Verilog\n\n**{mortos}/{len(resultados)} = {score:.1f}%**\n\n" + "\n".join(linhas) + "\n",
        encoding="utf-8")
    return 0 if score >= MINIMO else 1


if __name__ == "__main__":
    sys.exit(main())
