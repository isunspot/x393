/*******************************************************************************
 * Module: jp_channel
 * Date:2015-06-10  
 * Author: andrey     
 * Description: Top module of JPEG/JP4 compressor channel
 *
 * Copyright (c) 2015 <set up in Preferences-Verilog/VHDL Editor-Templates> .
 * jp_channel.v is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 *  jp_channel.v is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/> .
 *******************************************************************************/
`timescale 1ns/1ps

module  jp_channel#(
        parameter CMPRS_ADDR=                'h120, //TODO: assign valid adderss
        parameter CMPRS_MASK=                'h3f8,
        parameter CMPRS_CONTROL_REG=          0,
        parameter CMPRS_STATUS_CNTRL=         1,
        parameter CMPRS_FORMAT=               2,
        parameter CMPRS_COLOR_SATURATION=     3,
        parameter CMPRS_CORING_MODE=          4,
        parameter CMPRS_TABLES=               6, // 6..7
        parameter CMPRS_STATUS_REG_ADDR=     'h10,  //TODO: assign valid adderss

        parameter FRAME_HEIGHT_BITS=          16, // Maximal frame height 
        parameter LAST_FRAME_BITS=            16, // number of bits in frame counter (before rolls over)
        // Bit-fields in compressor control word
        parameter CMPRS_CBIT_RUN =            2, // bit # to control compressor run modes
        parameter CMPRS_CBIT_RUN_BITS =       2, // number of bits to control compressor run modes
        parameter CMPRS_CBIT_QBANK =          6, // bit # to control quantization table page
        parameter CMPRS_CBIT_QBANK_BITS =     3, // number of bits to control quantization table page
        parameter CMPRS_CBIT_DCSUB =          8, // bit # to control extracting DC components bypassing DCT
        parameter CMPRS_CBIT_DCSUB_BITS =     1, // bit # to control extracting DC components bypassing DCT
        parameter CMPRS_CBIT_CMODE =         13, // bit # to control compressor color modes
        parameter CMPRS_CBIT_CMODE_BITS =     4, // number of bits to control compressor color modes
        parameter CMPRS_CBIT_FRAMES =        15, // bit # to control compressor multi/single frame buffer modes
        parameter CMPRS_CBIT_FRAMES_BITS =    1, // number of bits to control compressor multi/single frame buffer modes
        parameter CMPRS_CBIT_BAYER =         20, // bit # to control compressor Bayer shift mode
        parameter CMPRS_CBIT_BAYER_BITS =     2, // number of bits to control compressor Bayer shift mode
        parameter CMPRS_CBIT_FOCUS =         23, // bit # to control compressor focus display mode
        parameter CMPRS_CBIT_FOCUS_BITS =     2, // number of bits to control compressor focus display mode
        // compressor bit-fields decode
        parameter CMPRS_CBIT_RUN_RST =        2'h0, // reset compressor, stop immediately
//      parameter CMPRS_CBIT_RUN_DISABLE =    2'h1, // disable compression of the new frames, finish any already started
        parameter CMPRS_CBIT_RUN_STANDALONE = 2'h2, // enable compressor, compress single frame from memory (async)
        parameter CMPRS_CBIT_RUN_ENABLE =     2'h3, // enable compressor, enable synchronous compression mode
        parameter CMPRS_CBIT_CMODE_JPEG18 =   4'h0, // color 4:2:0
        parameter CMPRS_CBIT_CMODE_MONO6 =    4'h1, // mono 4:2:0 (6 blocks)
        parameter CMPRS_CBIT_CMODE_JP46 =     4'h2, // jp4, 6 blocks, original
        parameter CMPRS_CBIT_CMODE_JP46DC =   4'h3, // jp4, 6 blocks, dc -improved
        parameter CMPRS_CBIT_CMODE_JPEG20 =   4'h4, // mono, 4 blocks (but still not actual monochrome JPEG as the blocks are scanned in 2x2 macroblocks)
        parameter CMPRS_CBIT_CMODE_JP4 =      4'h5, // jp4,  4 blocks, dc-improved
        parameter CMPRS_CBIT_CMODE_JP4DC =    4'h6, // jp4,  4 blocks, dc-improved
        parameter CMPRS_CBIT_CMODE_JP4DIFF =  4'h7, // jp4,  4 blocks, differential
        parameter CMPRS_CBIT_CMODE_JP4DIFFHDR =  4'h8, // jp4,  4 blocks, differential, hdr
        parameter CMPRS_CBIT_CMODE_JP4DIFFDIV2 = 4'h9, // jp4,  4 blocks, differential, divide by 2
        parameter CMPRS_CBIT_CMODE_JP4DIFFHDRDIV2 = 4'ha, // jp4,  4 blocks, differential, hdr,divide by 2
        parameter CMPRS_CBIT_CMODE_MONO1 =    4'hb, // mono JPEG (not yet implemented)
        parameter CMPRS_CBIT_CMODE_MONO4 =    4'he, // mono 4 blocks
        parameter CMPRS_CBIT_FRAMES_SINGLE =  0, //1, // use a single-frame buffer for images

        parameter CMPRS_COLOR18 =           0, // JPEG 4:2:0 with 18x18 overlapping tiles for de-bayer
        parameter CMPRS_COLOR20 =           1, // JPEG 4:2:0 with 18x18 overlapping tiles for de-bayer (not implemented)
        parameter CMPRS_MONO16 =            2, // JPEG 4:2:0 with 16x16 non-overlapping tiles, color components zeroed
        parameter CMPRS_JP4 =               3, // JP4 mode with 16x16 macroblocks
        parameter CMPRS_JP4DIFF =           4, // JP4DIFF mode TODO: see if correct
        parameter CMPRS_MONO8 =             7,  // Regular JPEG monochrome with 8x8 macroblocks (not yet implemented)
        
        parameter CMPRS_FRMT_MBCM1 =           0, // bit # of number of macroblock columns minus 1 field in format word
        parameter CMPRS_FRMT_MBCM1_BITS =     13, // number of bits in number of macroblock columns minus 1 field in format word
        parameter CMPRS_FRMT_MBRM1 =          13, // bit # of number of macroblock rows minus 1 field in format word
        parameter CMPRS_FRMT_MBRM1_BITS =     13, // number of bits in number of macroblock rows minus 1 field in format word
        parameter CMPRS_FRMT_LMARG =          26, // bit # of left margin field in format word
        parameter CMPRS_FRMT_LMARG_BITS =      5, // number of bits in left margin field in format word
        parameter CMPRS_CSAT_CB =              0, // bit # of number of blue scale field in color saturation word
        parameter CMPRS_CSAT_CB_BITS =        10, // number of bits in blue scale field in color saturation word
        parameter CMPRS_CSAT_CR =             12, // bit # of number of red scale field in color saturation word
        parameter CMPRS_CSAT_CR_BITS =        10, // number of bits in red scale field in color saturation word
        parameter CMPRS_CORING_BITS =          3,  // number of bits in coring mode
        
        parameter CMPRS_TIMEOUT_BITS=              12,
        parameter CMPRS_TIMEOUT=                   1000   // mclk cycles
        
        
)(
    input                         rst,    // global reset
    input                         xclk,   // global clock input, compressor single clock rate
    input                         xclk2x, // global clock input, compressor double clock rate, nominally rising edge aligned
    // programming interface
    input                         mclk,     // global system/memory clock
    input                   [7:0] cmd_ad,      // byte-serial command address/data (up to 6 bytes: AL-AH-D0-D1-D2-D3 
    input                         cmd_stb,     // strobe (with first byte) for the command a/d
    output                  [7:0] status_ad,   // status address/data - up to 5 bytes: A - {seq,status[1:0]} - status[2:9] - status[10:17] - status[18:25]
    output                        status_rq,   // input request to send status downstream
    input                         status_start, // Acknowledge of the first status packet byte (address)
    
    // Buffer interface (buffer to be a part of the memory controller - it is connected there by a 64-bit data, here - by an 9-bit one
    input                         xfer_reset_page_rd, // from mcntrl_tiled_rw (
    output                 [11:0] buf_ra,
    output                        buf_ren,
    output                        buf_regen,
    input                  [ 7:0] buf_di, 
    
    input                         page_ready_chn,     // single mclk (posedge)
    output                        next_page_chn,      // single mclk (posedge): Done with the page in the  buffer, memory controller may read more data 
// statistics data was not used in late nc353    
    input                         dccout,         //enable output of DC and HF components for brightness/color/focus adjustments
    input                   [2:0] hfc_sel,        // [2:0] (for autofocus) only components with both spacial frequencies higher than specified will be added
    output                        statistics_dv,
    output                 [15:0] statistics_do,

// Timestamp messages (@mclk)    
    input                         ts_pre_stb,  // @mclk - 1 cycle before receiving 8 bytes of timestamp data
    input                   [7:0] ts_data,     // timestamp data (s0,s1,s2,s3,us0,us1,us2,us3==0)
    
///    output [23:0] imgptr, - removed - use AFI channel MUX
    output                        eof_written_mclk,
    output                        stuffer_done_mclk,
    
    output                 [31:0] hifreq,             //  accumulated high frequency components in a frame sub-window
    input                         vsync_late,         // delayed start of frame, @xclk. In 353 it was 16 lines after VACT active
                                                      // source channel should already start, some delay give time for sequencer commands
                                                      // that should arrive before it
    output                        frame_start_dst,    // @mclk - trigger receive (tiledc) memory channel (it will take care of single/repetitive
                                                      // these output either follows vsync_late (reclocks it) or generated in non-bonded mode
                                                      // (compress from memory)
    input [FRAME_HEIGHT_BITS-1:0] line_unfinished_src,// number of the current (unfinished ) line, in the source (sensor) channel (RELATIVE TO FRAME, NOT WINDOW?)
    input   [LAST_FRAME_BITS-1:0] frame_number_src,   // current frame number (for multi-frame ranges) in the source (sensor) channel
    input                         frame_done_src,     // single-cycle pulse when the full frame (window) was transferred to/from DDR3 memory 
                                                      // frame_done_src is later than line_unfinished_src/ frame_number_src changes
                                                      // Used withe a single-frame buffers
     
    input [FRAME_HEIGHT_BITS-1:0] line_unfinished_dst,// number of the current (unfinished ) line in this (compressor) channel
    input   [LAST_FRAME_BITS-1:0] frame_number_dst,   // current frame number (for multi-frame ranges) in this (compressor channel
    input                         frame_done_dst,     // single-cycle pulse when the full frame (window) was transferred to/from DDR3 memory
                                                      // use as 'eot_real' in 353 
    output                        suspend,            // suspend reading data for this channel - waiting for the source data
    
    // Output interface to the AFI mux
    input                         hclk,
    input                         fifo_rst,      // reset FIFO (set read adderss to write, reset count)
    input                         fifo_ren,
    output                 [63:0] fifo_rdata,
    output                        fifo_eof,        // single rclk pulse signalling EOF
    input                         eof_written,   // confirm frame written ofer AFI to the system memory (single rclk pulse)
    output                        fifo_flush,    // EOF, need to output all what is in FIFO (Stays active until enough data chunks are read)
    output                 [7:0]  fifo_count     // number of 32-byte chunks in FIFO
);
    // Control signals to be defined
    wire                             frame_en;           // if 0 - will reset logic immediately (but not page number)
    wire                             stuffer_en;        //  extended enable to allow stuffer to gracefully finish 
    
    wire                             frame_go=frame_en;  // start frame: if idle, will start reading data (if available),
                                      // if running - will not restart a new frame if 0.
    wire [CMPRS_FRMT_LMARG_BITS-1:0] left_marg;          // left margin (for not-yet-implemented) mono JPEG (8 lines tile row) can need 7 bits (mod 32 - tile)
    wire [CMPRS_FRMT_MBCM1_BITS-1:0] n_blocks_in_row_m1; // number of macroblocks in a macroblock row minus 1
    wire [CMPRS_FRMT_MBRM1_BITS-1:0] n_block_rows_m1;    // number of macroblock rows in a frame minus 1
    wire                             ignore_color;       // zero Cb/Cr components (TODO: maybe include into converter_type?)
    wire                      [ 1:0] bayer_phase;        // [1:0])  bayer color filter phase 0:(GR/BG), 1:(RG/GB), 2: (BG/GR), 3: (GB/RG)
//    wire                             four_blocks;        // use only 6 blocks for the output, not 6
    wire                             jp4_dc_improved;    // in JP4 mode, compare DC coefficients to the same color ones
//    wire   [ 1:0] tile_margin;        // margins around 16x16 tiles (0/1/2)
//    wire   [ 2:0] tile_shift;         // tile shift from top left corner
    wire                      [ 2:0] converter_type;     // 0 - color18, 1 - color20, 2 - mono, 3 - jp4, 4 - jp4-diff, 7 - mono8 (not yet implemented)
    wire                             scale_diff;         // divide differences by 2 (to fit in 8-bit range)
    wire                             hdr;                // second green absolute, not difference
    wire                             subtract_dc;        // subtract/restore DC components
    wire    [CMPRS_CSAT_CB_BITS-1:0] m_cb;               // [9:0] scale for CB - default 0.564 (10'h90)
    wire    [CMPRS_CSAT_CR_BITS-1:0] m_cr;               // [9:0] scale for CR - default 0.713 (10'hb6)

    wire   [ 1:0] cmprs_fmode;        // focusing/overlay mode

    //TODO: assign next 5 values from converter_type[2:0]
    wire   [ 5:0] mb_w_m1;            // macroblock width minus 1 // 3 LSB not used, SHOULD BE SET to 3'b111
    wire   [ 5:0] mb_h_m1;            // macroblock horizontal period (8/16) // 3 LSB not used  SHOULD BE SET to 3'b111
    wire   [ 4:0] mb_hper;            // macroblock horizontal period (8/16) // 3 LSB not used TODO: assign from converter_type[2:0]
    wire   [ 1:0] tile_width;         // memory tile width (can be 128 for monochrome JPEG)   Can be 32/64/128: 0 - 16, 1 - 32, 2 - 64, 3 - 128
    wire          tile_col_width;     // 0 - 16 pixels,  1 -32 pixels
    
    
    // signals connecting modules: cmprs_macroblock_buf_iface_i and cmprs_pixel_buf_iface_i:
    wire          mb_pre_end;         // from cmprs_pixel_buf_iface - just in time to start a new macroblock w/o gaps
    wire          mb_release_buf;     // send required "next_page" pulses to buffer. Having rather long minimal latency in the memory
                                      // controller this can just be the same as mb_pre_end_in        
    wire          mb_pre_start;       // 1 clock cycle before stream of addresses to the buffer
    wire   [ 1:0] start_page;         // page to read next tile from (or first of several pages)
    wire   [ 6:0] macroblock_x;       // macroblock left pixel x relative to a tile (page) Maximal page - 128 bytes wide
    
    // signals connecting modules: cmprs_macroblock_buf_iface_i and cmprs_buf_average:
    
     wire         first_mb;           // output reg 
     wire         last_mb;            // output
    
    // signals connecting modules: cmprs_pixel_buf_iface_i and chn_rd_buf_i:
//    wire   [ 7:0] buf_di;             // data from the buffer
//    wire   [11:0] buf_ra;             // buffer read address (2 MSB - page number)
    wire   [ 1:0] buf_rd;             // buf {regen, re}
    
    
    // signals connecting modules: chn_rd_buf_i and ???:
    wire   [ 7:0] mb_data_out;       // Macroblock data out in scanline order 
    wire          mb_pre_first_out;  // Macroblock data out strobe - 1 cycle just before data valid
//    wire          mb_data_valid;     // Macroblock data out valid
    
    wire           limit_diff     = 1'b1;  // as in the prototype - just a constant 1
    
    // signals connecting modules: csconvert and cmprs_buf_average:
    
 
    wire   [8:0]  signed_y; // was y_in
    wire   [8:0]  signed_c; // was c_in
    wire   [7:0]  yaddrw; 
    wire          ywe; 
    wire   [7:0]  caddrw; 
    wire          cwe; 
    wire          yc_pre_first_out; // pre first output from color converter (was  pre_first_out) - last cycle of writing (may inc wpage
    // How they are used? Can it be average instead?  
    wire   [7:0]  n000;  // number of all 0 in macroblock (255 for 256), valid only for color JPEG 
    wire   [7:0]  n255;  // number of all 255 in macroblock (255 for 256), valid only for color JPEG 
    
    // signals connecting modules: cmprs_buf_average and ???:

    wire   [ 9:0] yc_nodc;         // [9:0] data out (4:2:0) (signed, average=0)
    wire   [ 8:0] yc_avr;          // [8:0]    DC (average value) - RAM output, no register. For Y components 9'h080..9'h07f, for C - 9'h100..9'h0ff!
//    wire          yc_nodc_dv;         // out data valid (will go high for at least 64 cycles)
    wire          dct_start;         // single-cycle mark of the first_r pixel in a 64 (8x8) - pixel block
    wire   [ 2:0] color_tn;   // [2:0] tile number 0..3 - Y, 4 - Cb, 5 - Cr (valid with start)
    wire          color_first;      // sending first_r MCU (valid @ ds)
    wire          color_last;       // sending last_r MCU (valid @ ds)
// below signals valid at ds ( 1 later than tn, first_r, last_r)
    wire    [2:0] component_num;    //[2:0] - component number (YCbCr: 0 - Y, 1 - Cb, 2 - Cr, JP4: 0-1-2-3 in sequence (depends on shift) 4 - don't use
    wire          component_color;  // use color quantization table (YCbCR, jp4diff)
    wire          component_first;  // first this component in a frame (DC absolute, otherwise - difference to previous)
    
    wire          component_lastinmb; // last_r component in a macroblock;


// control signals valid @ mclk
    wire          cmprs_en_extend;  // extend cmprs_en_xclk to include flushing
    wire          cmprs_en_mclk;    // resets immediately
    wire          cmprs_run_mclk;   // enable propagation of vsync_late to frame_start_dst in bonded(sync to src) mode
    wire          cmprs_standalone; // single-cycle: generate a single frame_start_dst in unbonded (not synchronized) mode. cmprs_run should be off
    wire          sigle_frame_buf;  // input - memory controller uses a single frame buffer (frame_number_* == 0), use other sync



    wire          force_flush_long; 
///    wire          enc_last; not used
    wire   [15:0] enc_do; 
    wire          enc_dv;

//TODO: use next signals for status
//    wire          eof_written_mclk;
//    wire          stuffer_done_mclk;
    wire          stuffer_running_mclk;
    wire          reading_frame;
    
///    wire          last_block; //huffman393
///    wire          test_lbw; 


    wire          stuffer_rdy; // receiver (bit stuffer) is ready to accept data;
    wire   [15:0] huff_do;     // output[15:0] reg 
    wire    [3:0] huff_dl;     // output[3:0] reg 
    wire          huff_dv;     // output reg 
    wire          flush;       // output reg @ negedge xclk2x
    


    wire   [31:0] cmd_data;       // 32-bit data to write to tables and registers(LSB first) - from cmd_deser
    wire          cmd_we;         // control register write enable
    wire   [2:0]  cmd_a;          // control register write enable
    
    wire          set_ctrl_reg_w;
    wire          set_status_w;
    wire          set_format_w;
    wire          set_color_saturation_w;
    wire          set_coring_w;
    wire          set_tables_w;
    
    wire          stuffer_running;   // @negedge xclk2x from registering timestamp until done
    
    wire   [12:0] quant_do; 
    wire          quant_ds;
    wire   [15:0] quant_dc_tdo;// MSB aligned coefficient for the DC component (used in focus module)
    wire   [ 2:0] cmprs_qpage;
    wire   [ 2:0] coring_num;
    reg           dcc_en;

    wire   [15:0] dccdata; // was not used in late nc353
    wire          dccvld;  // was not used in late nc353
    
    assign set_ctrl_reg_w =          cmd_we && (cmd_a==       CMPRS_CONTROL_REG);
    assign set_status_w =            cmd_we && (cmd_a==       CMPRS_STATUS_CNTRL);
    assign set_format_w =            cmd_we && (cmd_a==       CMPRS_FORMAT);
    assign set_color_saturation_w =  cmd_we && (cmd_a==       CMPRS_COLOR_SATURATION);
    assign set_coring_w =            cmd_we && (cmd_a==       CMPRS_CORING_MODE);
    assign set_tables_w =            cmd_we && ((cmd_a & 6)== CMPRS_TABLES);
    
    assign buf_ren =   buf_rd[0];
    assign buf_regen = buf_rd[1];
    
/*    
// Port buffer - TODO: Move to memory controller
    mcntrl_buf_rd #(
        .LOG2WIDTH_RD(3) // 64 bit external interface
    ) chn_rd_buf_i (
        .ext_clk      (xclk), // input
        .ext_raddr    (buf_ra), // input[11:0] 
        .ext_rd       (buf_rd[0]), // input
        .ext_regen    (buf_rd[1]), // input
        .ext_data_out (buf_di), // output[7:0] 
        .wclk         (!mclk), // input
        .wpage_in     (2'b0), // input[1:0] 
        .wpage_set    (xfer_reset_page_rd), // input  TODO: Generate @ negedge mclk on frame start
        .page_next    (buf_wpage_nxt), // input
        .page         (), // output[1:0]
        .we           (buf_wr), // input
        .data_in      (buf_wdata) // input[63:0] 
    );
*/

    cmd_deser #(
        .ADDR       (CMPRS_ADDR),
        .ADDR_MASK  (CMPRS_MASK),
        .NUM_CYCLES (6),
        .ADDR_WIDTH (3),
        .DATA_WIDTH (32)
    ) cmd_deser_32bit_i (
        .rst        (rst),      // input
        .clk        (mclk),     // input
        .ad         (cmd_ad),   // input[7:0] 
        .stb        (cmd_stb),  // input
        .addr       (cmd_a),    // output[3:0] 
        .data       (cmd_data), // output[31:0] 
        .we         (cmd_we)    // output
    );
    wire [2:0] status_data; 
    cmprs_status cmprs_status_i (
        .mclk            (mclk),                 // input
        .eof_written     (eof_written_mclk),     // input
        .stuffer_running (stuffer_running_mclk), // input
        .reading_frame   (reading_frame),        // input
        .status          (status_data)           // output[2:0] 
    );

    status_generate #(
        .STATUS_REG_ADDR  (CMPRS_STATUS_REG_ADDR),
        .PAYLOAD_BITS     (3)
    ) status_generate_i (
        .rst              (rst),           // input
        .clk              (mclk),          // input
        .we               (set_status_w),  // input
        .wd               (cmd_data[7:0]), // input[7:0] 
        .status           (status_data),   // input[2:0] 
        .ad               (status_ad),     // output[7:0] 
        .rq               (status_rq),     // output
        .start            (status_start)   // input
    );


    cmprs_cmd_decode #(
        .CMPRS_CBIT_RUN                  (CMPRS_CBIT_RUN),
        .CMPRS_CBIT_RUN_BITS             (CMPRS_CBIT_RUN_BITS),
        .CMPRS_CBIT_QBANK                (CMPRS_CBIT_QBANK),
        .CMPRS_CBIT_QBANK_BITS           (CMPRS_CBIT_QBANK_BITS),
        .CMPRS_CBIT_DCSUB                (CMPRS_CBIT_DCSUB),
        .CMPRS_CBIT_DCSUB_BITS           (CMPRS_CBIT_DCSUB_BITS),
        .CMPRS_CBIT_CMODE                (CMPRS_CBIT_CMODE),
        .CMPRS_CBIT_CMODE_BITS           (CMPRS_CBIT_CMODE_BITS),
        .CMPRS_CBIT_FRAMES               (CMPRS_CBIT_FRAMES),
        .CMPRS_CBIT_FRAMES_BITS          (CMPRS_CBIT_FRAMES_BITS),
        .CMPRS_CBIT_BAYER                (CMPRS_CBIT_BAYER),
        .CMPRS_CBIT_BAYER_BITS           (CMPRS_CBIT_BAYER_BITS),
        .CMPRS_CBIT_FOCUS                (CMPRS_CBIT_FOCUS),
        .CMPRS_CBIT_FOCUS_BITS           (CMPRS_CBIT_FOCUS_BITS),
        .CMPRS_CBIT_RUN_RST              (CMPRS_CBIT_RUN_RST),
        .CMPRS_CBIT_RUN_STANDALONE       (CMPRS_CBIT_RUN_STANDALONE),
        .CMPRS_CBIT_RUN_ENABLE           (CMPRS_CBIT_RUN_ENABLE),
        .CMPRS_CBIT_CMODE_JPEG18         (CMPRS_CBIT_CMODE_JPEG18),
        .CMPRS_CBIT_CMODE_MONO6          (CMPRS_CBIT_CMODE_MONO6),
        .CMPRS_CBIT_CMODE_JP46           (CMPRS_CBIT_CMODE_JP46),
        .CMPRS_CBIT_CMODE_JP46DC         (CMPRS_CBIT_CMODE_JP46DC),
        .CMPRS_CBIT_CMODE_JPEG20         (CMPRS_CBIT_CMODE_JPEG20),
        .CMPRS_CBIT_CMODE_JP4            (CMPRS_CBIT_CMODE_JP4),
        .CMPRS_CBIT_CMODE_JP4DC          (CMPRS_CBIT_CMODE_JP4DC),
        .CMPRS_CBIT_CMODE_JP4DIFF        (CMPRS_CBIT_CMODE_JP4DIFF),
        .CMPRS_CBIT_CMODE_JP4DIFFHDR     (CMPRS_CBIT_CMODE_JP4DIFFHDR),
        .CMPRS_CBIT_CMODE_JP4DIFFDIV2    (CMPRS_CBIT_CMODE_JP4DIFFDIV2),
        .CMPRS_CBIT_CMODE_JP4DIFFHDRDIV2 (CMPRS_CBIT_CMODE_JP4DIFFHDRDIV2),
        .CMPRS_CBIT_CMODE_MONO1          (CMPRS_CBIT_CMODE_MONO1),
        .CMPRS_CBIT_CMODE_MONO4          (CMPRS_CBIT_CMODE_MONO4),
        .CMPRS_CBIT_FRAMES_SINGLE        (CMPRS_CBIT_FRAMES_SINGLE),
        .CMPRS_COLOR18                   (CMPRS_COLOR18),
        .CMPRS_COLOR20                   (CMPRS_COLOR20),
        .CMPRS_MONO16                    (CMPRS_MONO16),
        .CMPRS_JP4                       (CMPRS_JP4),
        .CMPRS_JP4DIFF                   (CMPRS_JP4DIFF),
        .CMPRS_MONO8                     (CMPRS_MONO8),
        .CMPRS_FRMT_MBCM1                (CMPRS_FRMT_MBCM1),
        .CMPRS_FRMT_MBCM1_BITS           (CMPRS_FRMT_MBCM1_BITS),
        .CMPRS_FRMT_MBRM1                (CMPRS_FRMT_MBRM1),
        .CMPRS_FRMT_MBRM1_BITS           (CMPRS_FRMT_MBRM1_BITS),
        .CMPRS_FRMT_LMARG                (CMPRS_FRMT_LMARG),
        .CMPRS_FRMT_LMARG_BITS           (CMPRS_FRMT_LMARG_BITS),
        .CMPRS_CSAT_CB                   (CMPRS_CSAT_CB),
        .CMPRS_CSAT_CB_BITS              (CMPRS_CSAT_CB_BITS),
        .CMPRS_CSAT_CR                   (CMPRS_CSAT_CR),
        .CMPRS_CSAT_CR_BITS              (CMPRS_CSAT_CR_BITS),
        .CMPRS_CORING_BITS               (CMPRS_CORING_BITS)
    ) cmprs_cmd_decode_i (
        .rst                (rst),                 // input
        .xclk               (xclk),                // input - global clock input, compressor single clock rate
        .mclk               (mclk),                // input - global system/memory clock
        .ctrl_we            (set_ctrl_reg_w),      // input - control register write enable
        .format_we          (set_format_w),        // input - write number of tiles and left margin
        .color_sat_we       (set_color_saturation_w), // input - write color saturation values
        .coring_we          (set_coring_w),        // input - write color saturation values
        .di                 (cmd_data),            // input[31:0] - 32-bit data to write to control register (24LSB are used)
        .frame_start        (frame_start_dst),     // input @mclk
        .cmprs_en_mclk      (cmprs_en_mclk),       // output
        .cmprs_en_extend    (cmprs_en_extend),     // input
        .cmprs_run_mclk     (cmprs_run_mclk),      // output reg 
        .cmprs_standalone   (cmprs_standalone),    // output reg 
        .sigle_frame_buf    (sigle_frame_buf),     // output reg 
        .cmprs_en_xclk      (frame_en),            // output reg
        .cmprs_en_late_xclk (stuffer_en),          // output reg - extended enable to allow stuffer to gracefully finish 
        .cmprs_qpage        (cmprs_qpage),         // output[2:0] reg 
        .cmprs_dcsub        (subtract_dc),         // output reg 
        .cmprs_fmode        (cmprs_fmode),         // output[1:0] reg 
        .bayer_shift        (bayer_phase),         // output[1:0] reg 
        .ignore_color       (ignore_color),        // output reg 
//      .four_blocks        (four_blocks),         // output reg Not used?
        .four_blocks        (),                    // output reg Not used?
        .jp4_dc_improved    (jp4_dc_improved),     // output reg 
        .converter_type     (converter_type),      // output[2:0] reg 
        .scale_diff         (scale_diff),          // output reg 
        .hdr                (hdr),                 // output reg 
        .left_marg          (left_marg),           // output[4:0] reg 
        .n_blocks_in_row_m1 (n_blocks_in_row_m1),  // output[12:0] reg 
        .n_block_rows_m1    (n_block_rows_m1),     // output[12:0] reg 
        .color_sat_cb       (m_cb),                // output[9:0] reg 
        .color_sat_cr       (m_cr),                // output[9:0] reg 
        .coring             (coring_num)           // output[2:0] reg 
    );

// set derived parameters from converter_type
//    wire   [ 2:0] converter_type;    // 0 - color18, 1 - color20, 2 - mono, 3 - jp4, 4 - jp4-diff, 7 - mono8 (not yet implemented)
    cmprs_tile_mode_decode #( // fully combinatorial
        .CMPRS_COLOR18   (CMPRS_COLOR18),
        .CMPRS_COLOR20   (CMPRS_COLOR20),
        .CMPRS_MONO16    (CMPRS_MONO16),
        .CMPRS_JP4       (CMPRS_JP4),
        .CMPRS_JP4DIFF   (CMPRS_JP4DIFF),
        .CMPRS_MONO8     (CMPRS_MONO8)
    ) cmprs_tile_mode_decode_i (
        .converter_type  (converter_type), // input[2:0] 
        .mb_w_m1         (mb_w_m1),        // output[5:0] reg 
        .mb_h_m1         (mb_h_m1),        // output[5:0] reg 
        .mb_hper         (mb_hper),        // output[4:0] reg 
        .tile_width      (tile_width),     // output[1:0] reg 
        .tile_col_width  (tile_col_width)  // output reg 
    );


    cmprs_frame_sync #(
        .FRAME_HEIGHT_BITS  (FRAME_HEIGHT_BITS),
        .LAST_FRAME_BITS    (LAST_FRAME_BITS),
        .CMPRS_TIMEOUT_BITS (CMPRS_TIMEOUT_BITS),
        .CMPRS_TIMEOUT      (CMPRS_TIMEOUT)
    ) cmprs_frame_sync_i (
        .rst                (rst),                 // input
        .xclk               (xclk),                // input - global clock input, compressor single clock rate
        .mclk               (mclk),                // input - global system/memory clock
        .cmprs_en           (cmprs_en_mclk),       // input - @mclk 0 resets immediately
        .cmprs_en_extend    (cmprs_en_extend), // output
        .cmprs_run          (cmprs_run_mclk),      // input - @mclk enable propagation of vsync_late to frame_start_dst in bonded(sync to src) mode
        .cmprs_standalone   (cmprs_standalone),    // input - @mclk single-cycle: generate a single frame_start_dst in unbonded (not synchronized) mode.
                                                   // cmprs_run should be off
        .sigle_frame_buf    (sigle_frame_buf),     // input - memory controller uses a single frame buffer (frame_number_* == 0), use other sync
        .vsync_late         (vsync_late),          // input - @xclk delayed start of frame, @xclk. In 353 it was 16 lines after VACT active
                                                   // source channel should already start, some delay give time for sequencer commands
                                                   // that should arrive before it
        .frame_started      (first_mb && mb_pre_start), // @xclk started first macroblock (checking fro broken frames)
        .frame_start_dst    (frame_start_dst),     // output reg @mclk - trigger receive (tiled) memory channel (it will take care of
                                                   // single/repetitive modes itself this output either follows vsync_late (reclocks it)
                                                   // or generated in non-bonded mode (compress from memory once)
        .line_unfinished_src(line_unfinished_src), // input[15:0] - number of the current (unfinished ) line, in the source (sensor) channel
        .frame_number_src   (frame_number_src),    // input[15:0] - current frame number (for multi-frame ranges) in the source (sensor) channel
        .frame_done_src     (frame_done_src),      // input - single-cycle pulse when the full frame (window) was transferred to/from DDR3 memory 
                                                   // frame_done_src is later than line_unfinished_src/ frame_number_src changes
                                                   // Used withe a single-frame buffers
        .line_unfinished    (line_unfinished_dst), // input[15:0] - number of the current (unfinished ) line in this (compressor) channel
        .frame_number       (frame_number_dst),    // input[15:0] - current frame number (for multi-frame ranges) in this (compressor channel
        .frame_done         (frame_done_dst),      // input - single-cycle pulse when the full frame (window) was transferred to/from DDR3 memory 
        .suspend            (suspend),             // output reg - suspend reading data for this channel - waiting for the source data
        .stuffer_running    (stuffer_running), // input
        .force_flush_long   (force_flush_long),         // output reg - @ mclk tried to start frame compression before the previous one was finished
        .stuffer_running_mclk(stuffer_running_mclk), // output
        .reading_frame      (reading_frame) // output
        
    );

    cmprs_macroblock_buf_iface cmprs_macroblock_buf_iface_i (
        .rst                (rst), // input
        .xclk               (xclk), // input
        .mclk               (mclk), // input
        .xfer_reset_page_rd (xfer_reset_page_rd), // input
        .page_ready_chn     (page_ready_chn), // input
        .next_page_chn      (next_page_chn), // output
        .frame_en           (frame_en), // input
        .frame_go           (frame_go), // input - do not use - assign to frame_en? Running frames can be controlled by other means
        .left_marg          (left_marg), // input[4:0] 
        .n_blocks_in_row_m1 (n_blocks_in_row_m1), // input[12:0] 
        .n_block_rows_m1    (n_block_rows_m1), // input[12:0] 
        .mb_w_m1            (mb_w_m1),  // input[5:0]   // macroblock width minus 1 // 3 LSB not used - set them to all 1
        .mb_hper            (mb_hper),  // input[4:0]   // macroblock horizontal period (8/16) // 3 LSB not used (set them 0)
        .tile_width         (tile_width), // input[1:0]   // memory tile width. Can be 32/64/128: 0 - 16, 1 - 32, 2 - 64, 3 - 128
        .mb_pre_end_in      (mb_pre_end), // input
        .mb_release_buf     (mb_release_buf), // input
        .mb_pre_start_out   (mb_pre_start), // output
        .start_page         (start_page), // output[1:0] 
        .macroblock_x       (macroblock_x),  // output[6:0] 
        .first_mb           (first_mb), // output reg 
        .last_mb            (last_mb) // output
        
    );

    cmprs_pixel_buf_iface #(
        .CMPRS_PREEND_EARLY      (6), // TODO:Check / Adjust
        .CMPRS_RELEASE_EARLY     (16),
        .CMPRS_BUF_EXTRA_LATENCY (0),
        .CMPRS_COLOR18           (CMPRS_COLOR18),
        .CMPRS_COLOR20           (CMPRS_COLOR20),
        .CMPRS_MONO16            (CMPRS_MONO16),
        .CMPRS_JP4               (CMPRS_JP4),
        .CMPRS_JP4DIFF           (CMPRS_JP4DIFF),
        .CMPRS_MONO8             (CMPRS_MONO8)
         
    ) cmprs_pixel_buf_iface_i (
        .xclk               (xclk), // input
        .frame_en           (frame_en), // input
        .buf_di             (buf_di), // input[7:0] 
        .buf_ra             (buf_ra), // output[11:0] 
        .buf_rd             (buf_rd), // output[1:0] 
        .converter_type     (converter_type), // input[2:0] 
        .mb_w_m1            (mb_w_m1), // input[5:0] 
        .mb_h_m1            (mb_h_m1), // input[5:0] 
        .tile_width         (tile_width), // input[1:0] 
        .tile_col_width     (tile_col_width), // input
        .mb_pre_end         (mb_pre_end), // output
        .mb_release_buf     (mb_release_buf), // output
        .mb_pre_start       (mb_pre_start), // input
        .start_page         (start_page), // input[1:0] 
        .macroblock_x       (macroblock_x), // input[6:0] 
        .data_out           (mb_data_out), // output[7:0] // Macroblock data out in scanline order
        .pre_first_out      (mb_pre_first_out), // output // Macroblock data out strobe - 1 cycle just before data valid  == old pre_first_pixel?
//        .data_valid         (mb_data_valid) // output     // Macroblock data out valid
        .data_valid         () // output     // Macroblock data out valid Unused
    );

    csconvert #(
        .CMPRS_COLOR18   (CMPRS_COLOR18),
        .CMPRS_COLOR20   (CMPRS_COLOR20),
        .CMPRS_MONO16    (CMPRS_MONO16),
        .CMPRS_JP4       (CMPRS_JP4),
        .CMPRS_JP4DIFF   (CMPRS_JP4DIFF),
        .CMPRS_MONO8     (CMPRS_MONO8)
    ) csconvert_i (
        .xclk           (xclk),             // input
        .frame_en       (frame_en),         // input
        .converter_type (converter_type),   // input[2:0] 
        .ignore_color   (ignore_color),     // input
        .scale_diff     (scale_diff),       // input
        .hdr            (hdr),              // input
        .limit_diff     (limit_diff),       // input
        .m_cb           (m_cb),             // input[9:0] 
        .m_cr           (m_cr),             // input[9:0] 
        .mb_din         (mb_data_out),      // input[7:0] 
        .bayer_phase    (bayer_phase),      // input[1:0] 
        .pre_first_in   (mb_pre_first_out), // input
        .signed_y       (signed_y),         // output[8:0] reg 
        .signed_c       (signed_c),         // output[8:0] reg 
        .yaddrw         (yaddrw),           // output[7:0] reg 
        .ywe            (ywe),              // output reg 
        .caddrw         (caddrw),           // output[7:0] reg 
        .cwe            (cwe),              // output reg 
        .pre_first_out  (yc_pre_first_out), // output reg 
        .n000           (n000),             // output[7:0] reg 
        .n255           (n255)              // output[7:0] reg 
    );


    cmprs_buf_average #(
        .CMPRS_COLOR18   (CMPRS_COLOR18),
        .CMPRS_COLOR20   (CMPRS_COLOR20),
        .CMPRS_MONO16    (CMPRS_MONO16),
        .CMPRS_JP4       (CMPRS_JP4),
        .CMPRS_JP4DIFF   (CMPRS_JP4DIFF),
        .CMPRS_MONO8     (CMPRS_MONO8)
    ) cmprs_buf_average_i (
        .xclk               (xclk),             // input
        .frame_en           (frame_en),         // input
        .converter_type     (converter_type),   // input[2:0] 
        .pre_first_in       (mb_pre_first_out), // input
        .yc_pre_first_out   (yc_pre_first_out), // input
        .bayer_phase        (bayer_phase),      // input[1:0] 
        .jp4_dc_improved    (jp4_dc_improved),  // input
        .hdr                (hdr),              // input
        .subtract_dc_in     (subtract_dc),      // input
        .first_mb_in        (first_mb),         // input - calculate in cmprs_macroblock_buf_iface 
        .last_mb_in         (last_mb),          // input - calculate in cmprs_macroblock_buf_iface
        .yaddrw             (yaddrw),           // input[7:0] 
        .ywe                (ywe),              // input
        .signed_y           (signed_y),         // input[8:0] 
        .caddrw             (caddrw),           // input[7:0] 
        .cwe                (cwe),              // input
        .signed_c           (signed_c),         // input[8:0] 
        .do                 (yc_nodc),          // output[9:0] 
        .avr                (yc_avr),           // output[8:0] 
//        .dv                 (yc_nodc_dv),       // output
        .dv                 (),                 // output unused?
        .ds                 (dct_start),        // output
        .tn                 (color_tn),         // output[2:0] 
        .first              (color_first),      // output reg 
        .last               (color_last),       // output reg 
        .component_num      (component_num),    // output[2:0] 
        .component_color    (component_color),  // output
        .component_first    (component_first),  // output
        .component_lastinmb (component_lastinmb)// output reg 
    );
//  wire   [ 9:0] yc_nodc;         // [9:0] data out (4:2:0) (signed, average=0)


///TODO: Replace always@ with a module?

    wire          dct_last_in;
    wire          dct_pre_first_out;
//    wire          dct_dv;
    wire   [12:0] dct_out;
    
    
 //propagation of first block through compressor pipeline
 
    wire          first_block_color=(color_tn[2:0]==3'h0) && color_first;        // while color conversion,
    reg           first_block_color_after;  // after color conversion,
    reg           first_block_dct;     // after DCT
    wire          first_block_quant;   // after quantizer
    always @ (posedge xclk) begin
        if (dct_start)   first_block_color_after <= first_block_color;
        if (dct_last_in) first_block_dct   <= first_block_color_after;
    end
    
    
    
    
    xdct393 xdct393_i (
        .clk                (xclk), // input
        .en                 (frame_en), // input  if zero will reset transpose memory page numbers
        .start              (dct_start), // input  single-cycle start pulse that goes with the first pixel data. Other 63 should follow
        .xin                (yc_nodc), // input[9:0] 
        .last_in            (dct_last_in), // output reg  output high during input of the last of 64 pixels in a 8x8 block //
        .pre_first_out      (dct_pre_first_out), // outpu 1 cycle ahead of the first output in a 64 block
///        .dv                 (dct_dv), // output data output valid. Will go high on the 94-th cycle after the start (now - on 95-th?)
        .dv                 (),  // not used: output data output valid. Will go high on the 94-th cycle after the start (now - on 95-th?)
        .d_out              (dct_out) // output[12:0] 
    );
    wire          quant_start;
    dly_16 #(.WIDTH(1)) i_quant_start (.clk(xclk),.rst(1'b0), .dly(0), .din(dct_pre_first_out), .dout(quant_start));    // dly=0+1
 
    
    always @ (posedge xclk) begin
        if (!dccout) dcc_en <=1'b0;
        else if (dct_start && color_first && (color_tn[2:0]==3'b001)) dcc_en <=1'b1; // 3'b001 - closer to the first "start" in quantizator
    end
    
    
//    wire          table_a_not_d; // writing table address /not data (a[0] from cmd_deser)
//  wire          table_we;      // writing to tables               (decoded stb from cmd_deser)
    wire          tser_a_not_d;  // address/not data distributed to submodules
    wire   [ 7:0] tser_d;        // byte-wide serialized tables address/data to submodules
    wire          tser_qe;       // write serialized table data to quantizer
    wire          tser_ce;       // write serialized table data to coring
    wire          tser_fe;       // write serialized table data to focusing
    wire          tser_he;       // write serialized table data to Huffman
    
    table_ad_transmit #(
        .NUM_CHANNELS(4),
        .ADDR_BITS(3)
    ) table_ad_transmit_i (
        .clk             (mclk),                  // input @posedge
        .a_not_d_in      (cmd_a[0]),               // input writing table address /not data (a[0] from cmd_deser)
        .we              (set_tables_w),          // input writing to tables               (decoded stb from cmd_deser)
        .din             (cmd_data),              // input[31:0] 32-bit data to serialize/write to tables (LSB first) - from cmd_deser
        .ser_d           (tser_d),                // output[7:0] byte-wide serialized tables address/data to submodules
        .a_not_d         (tser_a_not_d),          // output reg address/not data distributed to submodules
        .chn_en          ({tser_he,tser_fe,tser_ce,tser_qe}) // output[0:0] reg - table 1-hot select outputs
    );
    
    
    
    quantizer393 quantizer393_i (
        .clk                (xclk),                   // input
        .en                 (frame_en),               // input 
        .mclk               (mclk),                   // input system clock, twqe, twce, ta,tdi - valid @posedge (ra, tdi - 2 cycles ahead (was negedge)
        .tser_qe            (tser_qe),                // input - write to a quantization table
        .tser_ce            (tser_ce),                // input - write to a coring table
        .tser_a_not_d       (tser_a_not_d),           // input - address/not data to tables
        .tser_d             (tser_d),                 // input[7:0] - byte-wide data to tables
        .ctypei             (component_color),        // input component type input (Y/C)
        .dci                (yc_avr),                 // input[8:0] - average value in a block - subtracted before DCT. now normal signed number
        .first_stb          (first_block_color),      // input - this is first stb pulse in a frame
        .stb                (dct_start),              // input - strobe that writes ctypei, dci
        .tsi                (cmprs_qpage[2:0]),       // input[2:0] - table (quality) select [2:0]
        .pre_start          (dct_pre_first_out),      // input - marks first input pixel (one before)
        .first_in           (first_block_dct),        // input - first block in (valid @ start)
        .first_out          (first_block_quant),      // output reg - valid @ ds
        .di                 (dct_out[12:0]),          // input[12:0] -  pixel data in (signed)
        .do                 (quant_do[12:0]),         // output[12:0] - pixel data out (AC is only 9 bits long?) - changed to 10
        .dv                 (),                       // output reg - data out valid
        .ds                 (quant_ds),               // output reg - data out strobe (one ahead of the start of dv)
        .dc_tdo             (quant_dc_tdo[15:0]),     // output[15:0] reg -  MSB aligned coefficient for the DC component (used in focus module)
        .dcc_en             (dcc_en),                 // input - enable dcc (sync to beginning of a new frame)
        .hfc_sel            (hfc_sel),                // input[2:0] - hight frequency components select [2:0] (includes components with both numbers >=hfc_sel
        .color_first        (color_first),            // input - first MCU in a frame
        .coring_num         (coring_num),             // input[2:0] - coring table pair number (0..7)
        .dcc_vld            (dccvld),                 // output reg  - single cycle when dcc_data is valid
        .dcc_data           (dccdata[15:0]),          // output[15:0] - dc component data out (for reading by software) 
        .n000               (n000),                   // input[7:0] - number of zero pixels (255 if 256) - to be multiplexed with dcc
        .n255               (n255)                    // input[7:0] - number of 0xff pixels (255 if 256) - to be multiplexed with dcc
    );

    // focus sharp module calculates amount of high-frequency components and optioanlly overlays/replaces actual image
    wire   [12:0] focus_do;     // output[12:0] reg  pixel data out, make timing ignore (valid 1.5 clk earlier that Quantizer output)
    wire          focus_ds;     // output reg data out strobe (one ahead of the start of dv)
    
    focus_sharp393 focus_sharp393_i (
        .clk                (xclk),                   // input - pixel clock
        .clk2x              (xclk2x),                 // input 2x pixel clock
        .en                 (frame_en),               // input 

        .mclk               (mclk),                   // input system clock to write tables
        .tser_we            (tser_fe),                // input - write to a quantization table
        .tser_a_not_d       (tser_a_not_d),           // input - address/not data to tables
        .tser_d             (tser_d),                 // input[7:0] - byte-wide data to tables
        
        .mode               (cmprs_fmode[1:0]),  // input[1:0] focus mode (combine image with focus info) - 0 - none, 1 - replace, 2 - combine all,  3 - combine woi
        .firsti             (color_first),            // input first macroblock
        .lasti              (color_last),             // input last macroblock
        .tni                (color_tn[2:0]),          // input[2:0] block number in a macronblock - 0..3 - Y, >=4 - color (sync to stb)
        .stb                (dct_start),              // input strobe that writes ctypei, dci
        .start              (quant_start),            // input marks first input pixel (needs 1 cycle delay from previous DCT stage)
        .di                 (dct_out),                // input[12:0] pixel data in (signed)
        .quant_ds           (quant_ds),               // input quantizator ds
        .quant_d            (quant_do[12:0]),         // input[12:0] quantizator data output
        .quant_dc_tdo       (quant_dc_tdo),           // input[15:0] MSB aligned coefficient for the DC component (used in focus module)
        .do                 (focus_do[12:0]),         // output[12:0] reg  pixel data out, make timing ignore (valid 1.5 clk earlier that Quantizer output)
        .ds                 (focus_ds),               // output reg data out strobe (one ahead of the start of dv)
        .hifreq             (hifreq[31:0])            // output[31:0] reg accumulated high frequency components in a frame sub-window
    );

    // Format DC components to be output as a mini-frame. Was not used in the late NC353 as the dma1 channel was use3d for IMU instead of dcc
    wire          finish_dcc;
    // re-sync to posedge xclk2x
    pulse_cross_clock finish_dcc_i (.rst(rst), .src_clk(~xclk2x), .dst_clk(xclk2x), .in_pulse(stuffer_done), .out_pulse(finish_dcc),.busy());
    
    dcc_sync393 dcc_sync393_i (
        .sclk               (xclk2x),                // input
        .dcc_en             (dcc_en),                // input xclk rising, sync with start of the frame
        .finish_dcc         (finish_dcc),            // input @ sclk rising
        .dcc_vld            (dccvld),                // input xclk rising
        .dcc_data           (dccdata[15:0]),         // input[15:0] @clk rising
        .statistics_dv      (statistics_dv),         // output reg 
        .statistics_do      (statistics_do[15:0])    // output[15:0] reg @ sclk
    );
    

// generate DC data/strobe for the direct output (re) using sdram channel3 buffering
// encoderDCAC is updated to handle 13-bit signed data instead of the 12-bit. It will limit the values on ot's own
    encoderDCAC393 encoderDCAC393_i (
        .clk                (xclk),                   // input
        .en                 (frame_en),               // input 
        .lasti              (color_last),             // input - was "last MCU in a frame" (@ stb)
        .first_blocki       (first_block_color),      // input - first block in frame - save fifo write address (@ stb)
        .comp_numberi       (component_num[2:0]),     // input[2:0] - component number 0..2 in color, 0..3 - in jp4diff, >= 4 - don't use (@ stb)
        .comp_firsti        (component_first),        // input - first this component in a frame (reset DC) (@ stb)
        .comp_colori        (component_color),        // input - use color - huffman? (@ stb)
        .comp_lastinmbi     (component_lastinmb),     // input - last component in a macroblock (@ stb) is it needed?
        .stb                (dct_start),              // input - strobe that writes firsti, lasti, tni,average
        .zdi                (focus_do[12:0]),         // input[12:0] - zigzag-reordered data input
        .first_blockz       (first_block_quant),      // input - first block input (@zds)
        .zds                (focus_ds),               // input - strobe - one ahead of the DC component output
///        .last               (enc_last),               // output reg 
        .last               (),                       // output reg - not used
        .do                 (enc_do[15:0]),           // output[15:0] reg 
        .dv                 (enc_dv)                  // output reg 
    );


    huffman393 i_huffman (
        .xclk               (xclk),                   // input
        .xclk2x             (xclk2x),                 // input
        .en                 (frame_en),               // input
        .mclk               (mclk),                   // input system clock to write tables
        .tser_we            (tser_he),                // input - write to a quantization table
        .tser_a_not_d       (tser_a_not_d),           // input - address/not data to tables
        .tser_d             (tser_d),                 // input[7:0] - byte-wide data to tables
        .di                 (enc_do[15:0]),           // input[15:0] - specially RLL prepared 16-bit data (to FIFO)
        .ds                 (enc_dv),                 // input -  di valid strobe
        .rdy                (stuffer_rdy),            // input - receiver (bit stuffer) is ready to accept data
        .do(huff_do[15:0]), // output[15:0] reg 
        .dl(huff_dl[3:0]), // output[3:0] reg 
        .dv(huff_dv), // output reg 
        .flush(flush), // output reg 
///        .last_block(last_block), // output reg 
        .last_block(), // output reg unused
        .test_lbw(), // output reg ??
///        .gotLastBlock(test_lbw) // output ??
        .gotLastBlock() // output ?? - unused (was for debug)
    );
    
    
    
    wire   [15:0] stuffer_do;
    wire          stuffer_dv;
    wire          stuffer_done;
    wire          eof_written_xclk2xn;

    stuffer393 stuffer393_i (
        .rst                 (rst),                    // input
        .mclk                (mclk),                   // input
        .ts_pre_stb          (ts_pre_stb),             // input      1 cycle before timestamp data, @mclk
        .ts_data             (ts_data),                // input[7:0] 8-byte timestamp data (s0,s1,s2,s3,us0,us1,us2,us3==0)
        .color_first         (color_first),            // input valid @xclk - only for sec/usec
        .fradv_clk           (xclk),                   // input
        .clk                 (xclk2x),                 // input clock - uses negedge inside
        .en_in               (stuffer_en),             // 
        .flush               (flush),                  // input - flush output data (fill byte with 0, long word with FFs)
        .abort               (force_flush_long),       // @ any, extracts 0->1 and flushes
        .stb                 (huff_dv),                // input
        .dl                  (huff_dl),                // input[3:0] number of bits to send (0 - 16) (0-16??)
        .d                   (huff_do),                // input[15:0] data to shift (only lower huff_dl bits are valid)
        // outputs valid @negedge xclk2x 
        .rdy                 (stuffer_rdy),            // output - enable huffman encoder to proceed. Used as CE for many huffman encoder registers
        .q                   (stuffer_do),             // output[15:0] reg - output data
        .qv                  (stuffer_dv),             // output reg - output data valid
        .done                (stuffer_done),           // output 
        .flushing            (),                       // output reg Not used?
        .running             (stuffer_running)         // from registering timestamp until done
        
`ifdef debug_stuffer
       ,.etrax_dma_r(tst_stuf_etrax[3:0]) // [3:0] just for testing
       ,.test_cntr(test_cntr[3:0])
       ,.test_cntr1(test_cntr1[7:0])
`endif
    );
    
    pulse_cross_clock stuffer_done_mclk_i (.rst(rst), .src_clk(~xclk2x), .dst_clk(mclk), .in_pulse(stuffer_done), .out_pulse(stuffer_done_mclk),.busy());
    cmprs_out_fifo cmprs_out_fifo_i (
        .rst                 (rst),            // input mostly for simulation
        // source (stuffer) clock domain
        .wclk                (~xclk2x),        // input source clock (2x pixel clock, inverted) - same as stuffer out
        .we                  (stuffer_dv),     // input write data from stuffer
        .wdata               (stuffer_do),     // input[15:0] data from stuffer module;
        .wa_rst              (!stuffer_en),    // input reset low address bits when stuffer is disabled (to make sure it is multiple of 32 bytes
        .wlast               (stuffer_done),   // input - written last 32 bytes of a frame (flush FIFO) - stuffer_done (has to be later than we)
        .eof_written_wclk    (eof_written_xclk2xn),    // output - AFI had transferred frame data to the system memory
        .rclk                (hclk),           // input - AFI clock
        // AFI clock domain
        .rst_fifo            (fifo_rst),       // input - reset FIFO (set read adderss to write, reset count)
        .ren                 (fifo_ren),       // input - fifo read from AFI channel mux
        .rdata               (fifo_rdata),     // output[63:0] - data to AFI channel mux (latency == 2 from fifo_ren)
        .eof                 (fifo_eof),       // output single hclk pulse signalling EOF
        .eof_written         (eof_written),    // input single hclk pulse confirming frame data is written to the system memory
        .flush_fifo          (fifo_flush),     // output level signalling that FIFO has data from the current frame (use short AXI burst if needed)
        .fifo_count          (fifo_count)      // output[7:0] - number of 32-byte chunks available in FIFO
    );
    pulse_cross_clock eof_written_mclk_i (.rst(rst), .src_clk(~xclk2x), .dst_clk(mclk), .in_pulse(eof_written_xclk2xn), .out_pulse(eof_written_mclk),.busy());

// TODO: Add status module to combine/FF, re-clock status signals


endmodule

