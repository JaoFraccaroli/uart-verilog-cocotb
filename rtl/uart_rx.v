// Receptor UART 8N1.
//
// - Sincroniza a entrada com dois flip-flops (a linha vem de fora do chip).
// - Confirma o bit de início no meio do bit: um pulso curto de ruído não
//   é confundido com um byte.
// - Lê cada bit de dados no meio do bit.
// - Se o bit de parada vier 0, sinaliza erro de quadro em vez de entregar o byte.
module uart_rx #(
    parameter CLKS_POR_BIT = 234
) (
    input  wire       clk,
    input  wire       rst,          // reset síncrono, ativo em 1
    input  wire       rx,           // linha serial (repouso = 1)
    output reg  [7:0] dado,
    output reg        valido,       // pulso de 1 ciclo: dado recebido sem erro
    output reg        erro_quadro   // pulso de 1 ciclo: bit de parada inválido
);
    localparam OCIOSO = 2'd0, INICIO = 2'd1, DADOS = 2'd2, PARADA = 2'd3;
    localparam LARGURA_CONTADOR = $clog2(CLKS_POR_BIT + 1);
    localparam MEIO_DO_BIT = (CLKS_POR_BIT - 1) / 2;

    reg [1:0]                  estado;
    reg [LARGURA_CONTADOR-1:0] ciclos;
    reg [2:0]                  indice;
    reg [7:0]                  buffer;
    reg                        rx_meta, rx_sinc;

    // Sincronizador de 2 estágios
    always @(posedge clk) begin
        if (rst) begin
            rx_meta <= 1'b1;
            rx_sinc <= 1'b1;
        end else begin
            rx_meta <= rx;
            rx_sinc <= rx_meta;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            estado      <= OCIOSO;
            ciclos      <= 0;
            indice      <= 0;
            buffer      <= 8'h00;
            dado        <= 8'h00;
            valido      <= 1'b0;
            erro_quadro <= 1'b0;
        end else begin
            valido      <= 1'b0;
            erro_quadro <= 1'b0;
            case (estado)
                OCIOSO: begin
                    ciclos <= 0;
                    indice <= 0;
                    if (rx_sinc == 1'b0)
                        estado <= INICIO;
                end
                INICIO: begin
                    if (ciclos == MEIO_DO_BIT) begin
                        ciclos <= 0;
                        // Ainda em 0 no meio do bit: é um início de verdade
                        estado <= (rx_sinc == 1'b0) ? DADOS : OCIOSO;
                    end else
                        ciclos <= ciclos + 1'b1;
                end
                DADOS: begin
                    if (ciclos == CLKS_POR_BIT - 1) begin
                        ciclos         <= 0;
                        buffer[indice] <= rx_sinc;
                        if (indice == 3'd7)
                            estado <= PARADA;
                        else
                            indice <= indice + 1'b1;
                    end else
                        ciclos <= ciclos + 1'b1;
                end
                PARADA: begin
                    if (ciclos == CLKS_POR_BIT - 1) begin
                        ciclos <= 0;
                        estado <= OCIOSO;
                        if (rx_sinc == 1'b1) begin
                            dado   <= buffer;
                            valido <= 1'b1;
                        end else
                            erro_quadro <= 1'b1;
                    end else
                        ciclos <= ciclos + 1'b1;
                end
            endcase
        end
    end
endmodule
