module traffic_light_controller (
    input wire clk,
    input wire rst_n,
    input wire emerg_north,
    input wire emerg_south,
    input wire emerg_east,
    input wire emerg_west,
    output reg [2:0] light_north,
    output reg [2:0] light_south,
    output reg [2:0] light_east,
    output reg [2:0] light_west
);

    // State Encoding
    localparam S_NS_GREEN  = 3'd0;
    localparam S_NS_YELLOW = 3'd1;
    localparam S_EW_GREEN  = 3'd2;
    localparam S_EW_YELLOW = 3'd3;
    localparam S_EMERG_NS  = 3'd4;
    localparam S_EMERG_EW  = 3'd5;

    // Light Colors
    localparam RED    = 3'b100;
    localparam YELLOW = 3'b010;
    localparam GREEN  = 3'b001;

    // Timing Parameters (simplified for demo)
    localparam TIME_GREEN  = 4'd10;
    localparam TIME_YELLOW = 4'd3;

    reg [2:0] current_state, next_state;
    reg [3:0] timer;

    // Timer Logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            timer <= 0;
        end else begin
            if (current_state != next_state) begin
                timer <= 0; 
            end else begin
                timer <= timer + 1;
            end
        end
    end

    // State Transition Logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= S_NS_GREEN;
        end else begin
            current_state <= next_state;
        end
    end

    // Next State Logic
    always @(*) begin
        next_state = current_state; 

        // Emergency Override Logic
        // Priority: North/South > East/West
        
        if (emerg_north || emerg_south) begin
            case (current_state)
                S_EW_GREEN: next_state = S_EW_YELLOW; 
                S_EW_YELLOW: begin
                     if (timer >= TIME_YELLOW) next_state = S_EMERG_NS;
                end
                S_NS_GREEN: next_state = S_EMERG_NS; 
                S_NS_YELLOW: next_state = S_EMERG_NS; 
                S_EMERG_EW: next_state = S_EW_YELLOW; 
                S_EMERG_NS: next_state = S_EMERG_NS; 
                default: next_state = S_EMERG_NS;
            endcase
        end
        else if (emerg_east || emerg_west) begin
            case (current_state)
                S_NS_GREEN: next_state = S_NS_YELLOW; 
                S_NS_YELLOW: begin
                    if (timer >= TIME_YELLOW) next_state = S_EMERG_EW;
                end
                S_EW_GREEN: next_state = S_EMERG_EW; 
                S_EW_YELLOW: next_state = S_EMERG_EW; 
                S_EMERG_NS: next_state = S_NS_YELLOW; 
                S_EMERG_EW: next_state = S_EMERG_EW; 
                default: next_state = S_EMERG_EW;
            endcase
        end
        else begin
            // Normal Operation
            case (current_state)
                S_NS_GREEN: begin
                    if (timer >= TIME_GREEN) next_state = S_NS_YELLOW;
                end
                S_NS_YELLOW: begin
                    if (timer >= TIME_YELLOW) next_state = S_EW_GREEN;
                end
                S_EW_GREEN: begin
                    if (timer >= TIME_GREEN) next_state = S_EW_YELLOW;
                end
                S_EW_YELLOW: begin
                    if (timer >= TIME_YELLOW) next_state = S_NS_GREEN;
                end
                S_EMERG_NS: next_state = S_NS_GREEN; 
                S_EMERG_EW: next_state = S_EW_GREEN;
                default: next_state = S_NS_GREEN;
            endcase
        end
    end

    // Output Logic
    always @(*) begin
        light_north = RED;
        light_south = RED;
        light_east = RED;
        light_west = RED;

        case (current_state)
            S_NS_GREEN, S_EMERG_NS: begin
                light_north = GREEN;
                light_south = GREEN;
                light_east = RED;
                light_west = RED;
            end
            S_NS_YELLOW: begin
                light_north = YELLOW;
                light_south = YELLOW;
                light_east = RED;
                light_west = RED;
            end
            S_EW_GREEN, S_EMERG_EW: begin
                light_north = RED;
                light_south = RED;
                light_east = GREEN;
                light_west = GREEN;
            end
            S_EW_YELLOW: begin
                light_north = RED;
                light_south = RED;
                light_east = YELLOW;
                light_west = YELLOW;
            end
        endcase
    end

endmodule
