// Circuito completo para a placa Tang Nano 9K: tudo o que chega pela
// serial volta para o computador (eco), e os LEDs mostram o último byte.
//
// Usa um buffer de 1 byte: se um byte novo chegar enquanto o anterior
// ainda está saindo, ele espera em vez de se perder.
module eco_uart #(
    parameter CLKS_POR_BIT = 234   // 27 MHz / 115200 baud
) (
    input  wire       clk,
    input  wire       botao_reset_n, // botão da placa: 0 quando apertado
    input  wire       uart_rx,
    output wire       uart_tx,
    output wire [5:0] leds_n         // LEDs da Tang Nano 9K acendem em 0
);
    wire       rst = ~botao_reset_n;
    wire [7:0] recebido;
    wire       recebido_valido;
    wire       erro_quadro;
    wire       tx_ocupado;

    reg  [7:0] pendente;
    reg        tem_pendente;
    reg        enviar;
    reg  [7:0] ultimo;

    uart_rx #(.CLKS_POR_BIT(CLKS_POR_BIT)) receptor (
        .clk(clk), .rst(rst), .rx(uart_rx),
        .dado(recebido), .valido(recebido_valido), .erro_quadro(erro_quadro)
    );

    uart_tx #(.CLKS_POR_BIT(CLKS_POR_BIT)) transmissor (
        .clk(clk), .rst(rst), .enviar(enviar), .dado(pendente),
        .tx(uart_tx), .ocupado(tx_ocupado)
    );

    always @(posedge clk) begin
        if (rst) begin
            pendente     <= 8'h00;
            tem_pendente <= 1'b0;
            enviar       <= 1'b0;
            ultimo       <= 8'h00;
        end else begin
            enviar <= 1'b0;
            if (recebido_valido) begin
                pendente     <= recebido;
                tem_pendente <= 1'b1;
                ultimo       <= recebido;
            end else if (tem_pendente && !tx_ocupado && !enviar) begin
                enviar       <= 1'b1;
                tem_pendente <= 1'b0;
            end
        end
    end

    assign leds_n = ~ultimo[5:0];
endmodule
