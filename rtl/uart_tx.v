// Transmissor UART 8N1: 1 bit de início (0), 8 bits de dados (o menos
// significativo primeiro) e 1 bit de parada (1). Sem paridade.
//
// CLKS_POR_BIT = frequência do clock / baud rate
//   Tang Nano 9K: 27 MHz / 115200 = 234
module uart_tx #(
    parameter CLKS_POR_BIT = 234
) (
    input  wire       clk,
    input  wire       rst,      // reset síncrono, ativo em 1
    input  wire       enviar,   // pulso de 1 ciclo para começar a transmissão
    input  wire [7:0] dado,
    output reg        tx,       // linha serial (repouso = 1)
    output wire       ocupado   // 1 enquanto um byte está sendo transmitido
);
    localparam OCIOSO = 2'd0, INICIO = 2'd1, DADOS = 2'd2, PARADA = 2'd3;
    localparam LARGURA_CONTADOR = $clog2(CLKS_POR_BIT + 1);

    reg [1:0]                  estado;
    reg [LARGURA_CONTADOR-1:0] ciclos;
    reg [2:0]                  indice;
    reg [7:0]                  buffer;

    assign ocupado = (estado != OCIOSO);

    always @(posedge clk) begin
        if (rst) begin
            estado <= OCIOSO;
            tx     <= 1'b1;
            ciclos <= 0;
            indice <= 0;
            buffer <= 8'h00;
        end else begin
            case (estado)
                OCIOSO: begin
                    tx     <= 1'b1;
                    ciclos <= 0;
                    indice <= 0;
                    if (enviar) begin
                        buffer <= dado;   // guarda o dado: pode mudar durante o envio
                        tx     <= 1'b0;   // bit de início
                        estado <= INICIO;
                    end
                end
                INICIO: begin
                    if (ciclos == CLKS_POR_BIT - 1) begin
                        ciclos <= 0;
                        tx     <= buffer[0];
                        estado <= DADOS;
                    end else
                        ciclos <= ciclos + 1'b1;
                end
                DADOS: begin
                    if (ciclos == CLKS_POR_BIT - 1) begin
                        ciclos <= 0;
                        if (indice == 3'd7) begin
                            tx     <= 1'b1;  // bit de parada
                            estado <= PARADA;
                        end else begin
                            indice <= indice + 1'b1;
                            tx     <= buffer[indice + 1'b1];
                        end
                    end else
                        ciclos <= ciclos + 1'b1;
                end
                PARADA: begin
                    if (ciclos == CLKS_POR_BIT - 1) begin
                        ciclos <= 0;
                        estado <= OCIOSO;
                    end else
                        ciclos <= ciclos + 1'b1;
                end
            endcase
        end
    end
endmodule
