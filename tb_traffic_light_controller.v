`timescale 1ns / 1ps

module tb_traffic_light_controller;

    // Inputs
    reg clk;
    reg rst_n;
    reg emerg_north;
    reg emerg_south;
    reg emerg_east;
    reg emerg_west;

    // Outputs
    wire [2:0] light_north;
    wire [2:0] light_south;
    wire [2:0] light_east;
    wire [2:0] light_west;

    // Instantiate the Unit Under Test (UUT)
    traffic_light_controller uut (
        .clk(clk),
        .rst_n(rst_n),
        .emerg_north(emerg_north),
        .emerg_south(emerg_south),
        .emerg_east(emerg_east),
        .emerg_west(emerg_west),
        .light_north(light_north),
        .light_south(light_south),
        .light_east(light_east),
        .light_west(light_west)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns period
    end

    // Helper task to display the intersection
    task display_intersection;
        input [2:0] n, s, e, w;
        reg [7:0] str_n, str_s, str_e, str_w;
        begin
            // Convert 3-bit color to character string
            case(n) 3'b100: str_n = "R"; 3'b010: str_n = "Y"; 3'b001: str_n = "G"; default: str_n = "?"; endcase
            case(s) 3'b100: str_s = "R"; 3'b010: str_s = "Y"; 3'b001: str_s = "G"; default: str_s = "?"; endcase
            case(e) 3'b100: str_e = "R"; 3'b010: str_e = "Y"; 3'b001: str_e = "G"; default: str_e = "?"; endcase
            case(w) 3'b100: str_w = "R"; 3'b010: str_w = "Y"; 3'b001: str_w = "G"; default: str_w = "?"; endcase

            $display("Time: %0t ns", $time);
            $display("      N: [%s]", str_n);
            $display("W: [%s]       E: [%s]", str_w, str_e);
            $display("      S: [%s]", str_s);
            $display("---------------------");
        end
    endtask

    // Stimulus
    initial begin
        // Initialize Inputs
        rst_n = 0;
        emerg_north = 0;
        emerg_south = 0;
        emerg_east = 0;
        emerg_west = 0;

        // Wait for global reset
        #20;
        rst_n = 1;

        $display("Starting Normal Operation...");
        // Run for a while to see normal cycling
        repeat(30) @(posedge clk);

        $display("!!! EMG: Ambulance from NORTH !!!");
        emerg_north = 1;
        repeat(20) @(posedge clk); 
        emerg_north = 0; // Emergency passed
        $display("Emergency Cleared.");
        
        repeat(15) @(posedge clk); // Back to normal

        $display("!!! EMG: Fire Truck from EAST !!!");
        emerg_east = 1;
        repeat(20) @(posedge clk);
        emerg_east = 0;
        $display("Emergency Cleared.");

        repeat(20) @(posedge clk);

        $finish;
    end

    // Visualization loop
    always @(posedge clk) begin
        display_intersection(light_north, light_south, light_east, light_west);
    end

    // Waveform dump
    initial begin
        $dumpfile("traffic_light.vcd");
        $dumpvars(0, tb_traffic_light_controller);
    end

endmodule
