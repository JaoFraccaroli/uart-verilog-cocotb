// Contador binário com habilitação e reset síncrono.
// Primeiro circuito do projeto: simples o bastante para aprender o fluxo
// "escrever Verilog -> simular -> testar em Python".
module contador #(
    parameter LARGURA = 4
) (
    input  wire               clk,
    input  wire               rst,       // reset síncrono, ativo em 1
    input  wire               habilita,  // só conta quando habilita = 1
    output reg  [LARGURA-1:0] valor,
    output wire               estouro    // 1 no ciclo em que o contador volta para zero
);
    assign estouro = habilita && (valor == {LARGURA{1'b1}});

    always @(posedge clk) begin
        if (rst)
            valor <= {LARGURA{1'b0}};
        else if (habilita)
            valor <= valor + 1'b1;
    end
endmodule
