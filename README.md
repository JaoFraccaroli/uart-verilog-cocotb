# UART em Verilog testada com cocotb

![Testes](https://github.com/JaoFraccaroli/uart-verilog-cocotb/actions/workflows/testes.yml/badge.svg)

Primeiro projeto da minha trilha de **microeletrônica**. São circuitos digitais em **Verilog**, e cada um é verificado por uma bateria de **testes automatizados em Python** com o **cocotb**. Esse é o mesmo trabalho de *verificação* feito em projeto de chips: provar com testes que o circuito faz o que deveria, antes de ir para o hardware.

| Métrica | Resultado |
|---|---|
| Testes de simulação (cocotb) | 56 passando, em 9 configurações do circuito |
| Testes do modelo de referência (Pytest) | 10 passando |
| Teste de mutação no Verilog | 14 de 14 mutantes mortos (100%) |

## Circuitos

| Arquivo | O que faz |
|---|---|
| [`rtl/contador.v`](rtl/contador.v) | Contador com reset, habilita e sinal de estouro. É o "olá mundo" do projeto |
| [`rtl/uart_tx.v`](rtl/uart_tx.v) | Transmissor serial UART 8N1 |
| [`rtl/uart_rx.v`](rtl/uart_rx.v) | Receptor UART com sincronizador, filtro de ruído no bit de início e detecção de erro de quadro |
| [`rtl/eco_uart.v`](rtl/eco_uart.v) | Circuito completo para a placa **Tang Nano 9K**: devolve tudo o que chega pela serial e mostra o último byte nos LEDs |

A UART é a comunicação serial mais básica que existe: é como a placa conversa com o computador pelo cabo USB. Cada byte vai em um **quadro** de 10 bits: início (0), 8 bits de dados, do menos significativo para o mais significativo, e parada (1).

## Como os testes funcionam

```
Python (cocotb)  ──>  simulador (Icarus Verilog)  ──>  circuito em Verilog
   testes e            roda o circuito ciclo a ciclo
 modelo de referência
```

- [`testes/modelos.py`](testes/modelos.py): **modelo de referência**, o "outro lado do cabo". Envia e lê bits na temporização de uma UART de verdade.
- [`testes/tb_*.py`](testes): os testes de cada circuito.
- [`testes/test_simulacao.py`](testes/test_simulacao.py): liga tudo ao **Pytest** e roda cada circuito com vários valores de `CLKS_POR_BIT`, para provar que o circuito funciona em mais de uma velocidade.

### O que é testado

| Circuito | Casos |
|---|---|
| Contador | reset; conta 1 por ciclo; sem habilita não muda; volta a zero depois do máximo (fronteira); estouro só com habilita; reset tem prioridade |
| Transmissor | linha em repouso = 1; bytes de fronteira (0x00, 0xFF, 0x01, 0x80, 0x55, 0xAA...); **todos os 256 bytes**; quadro dura exatamente 10 bits; bit menos significativo primeiro; pedido no meio do envio é ignorado; dado pode mudar durante o envio; reset no meio |
| Receptor | bytes de fronteira e os 256 bytes em sequência; `valido` dura exatamente 1 ciclo; bit de parada errado gera erro de quadro; ruído curto não vira byte; volta a funcionar depois de um erro; **tolera relógio ±3% diferente**; diferença de ~12% não passa despercebida |
| Eco (placa) | mensagem inteira sem pausa entre bytes volta sem perda; LEDs mostram o último byte; botão de reset |

### Teste de mutação

O [`qualidade/mutacao.py`](qualidade/mutacao.py) planta 14 erros no Verilog, do tipo que acontece de verdade: bit mais significativo primeiro, contador errado por um ciclo, receptor que não confere o bit de parada, eco sem buffer. Para cada erro, confere se algum teste falha. Todos foram detectados.

## Como rodar

No Linux, ou no Windows pelo **WSL2** (Ubuntu dentro do Windows):

```bash
sudo apt install iverilog          # simulador
pip install -r requirements.txt    # cocotb e pytest

pytest                             # roda todos os testes
python qualidade/mutacao.py        # teste de mutação
```

As **formas de onda** de cada simulação ficam em `sim_build/*/*.fst`. Abra no [GTKWave](https://gtkwave.sourceforge.net/) ou no [Surfer](https://surfer-project.org/) para ver os sinais bit a bit. No GitHub Actions, elas ficam disponíveis para download em *Artifacts*.

## Na placa (próximo passo)

O arquivo [`placa/tang_nano_9k.cst`](placa/tang_nano_9k.cst) liga o `eco_uart` aos pinos da **Sipeed Tang Nano 9K** (27 MHz, 115200 baud). **Ainda não foi testado na placa**: confira os pinos na documentação da Sipeed antes de gravar. A ideia é gravar com o Gowin EDA ou com as ferramentas abertas (Yosys, nextpnr e openFPGALoader), abrir um terminal serial no computador e ver o eco funcionando.

## Próximos passos da trilha
- [ ] Gravar o `eco_uart` na Tang Nano 9K
- [ ] Saída de vídeo VGA/HDMI
- [ ] Uma mini-CPU, com testes do conjunto de instruções em cocotb
- [ ] Cobertura funcional dos testes
