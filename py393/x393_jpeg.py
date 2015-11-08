from __future__ import division
from __future__ import print_function

'''
# Copyright (C) 2015, Elphel.inc.
# Class to generate JPEG headers/tables and compose JPEG files from
# the compressed by the FPGA data in memory
#   
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http:#www.gnu.org/licenses/>.

@author:     Andrey Filippov
@copyright:  2015 Elphel, Inc.
@license:    GPLv3.0+
@contact:    andrey@elphel.coml
@deffield    updated: Updated
'''
__author__ = "Andrey Filippov"
__copyright__ = "Copyright 2015, Elphel, Inc."
__license__ = "GPL"
__version__ = "3.0+"
__maintainer__ = "Andrey Filippov"
__email__ = "andrey@elphel.com"
__status__ = "Development"
#import sys
#import pickle
from x393_mem                import X393Mem
import x393_axi_control_status
import x393_utils
#import time
import x393_sens_cmprs
import x393_cmprs_afi
import vrlg
STD_QUANT_TBLS = {
                  "Y_landscape":( 16,  11,  10,  16,  24,  40,  51,  61,
                                  12,  12,  14,  19,  26,  58,  60,  55,
                                  14,  13,  16,  24,  40,  57,  69,  56,
                                  14,  17,  22,  29,  51,  87,  80,  62,
                                  18,  22,  37,  56,  68, 109, 103,  77,
                                  24,  35,  55,  64,  81, 104, 113,  92,
                                  49,  64,  78,  87, 103, 121, 120, 101,
                                  72,  92,  95,  98, 112, 100, 103,  99),
                  "C_landscape":( 17,  18,  24,  47,  99,  99,  99,  99,
                                  18,  21,  26,  66,  99,  99,  99,  99,
                                  24,  26,  56,  99,  99,  99,  99,  99,
                                  47,  66,  99,  99,  99,  99,  99,  99,
                                  99,  99,  99,  99,  99,  99,  99,  99,
                                  99,  99,  99,  99,  99,  99,  99,  99,
                                  99,  99,  99,  99,  99,  99,  99,  99,
                                  99,  99,  99,  99,  99,  99,  99,  99),
                  "Y_portrait": ( 16,  12,  14,  14,  18,  24,  49,  72,
                                  11,  12,  13,  17,  22,  35,  64,  92,
                                  10,  14,  16,  22,  37,  55,  78,  95,
                                  16,  19,  24,  29,  56,  64,  87,  98,
                                  24,  26,  40,  51,  68,  81, 103, 112,
                                  40,  58,  57,  87, 109, 104, 121, 100,
                                  51,  60,  69,  80, 103, 113, 120, 103,
                                  61,  55,  56,  62,  77,  92, 101,  99),
                  "C_portrait": ( 17,  18,  24,  47,  99,  99,  99,  99,
                                  18,  21,  26,  66,  99,  99,  99,  99,
                                  24,  26,  56,  99,  99,  99,  99,  99,
                                  47,  66,  99,  99,  99,  99,  99,  99,
                                  99,  99,  99,  99,  99,  99,  99,  99,
                                  99,  99,  99,  99,  99,  99,  99,  99,
                                  99,  99,  99,  99,  99,  99,  99,  99,
                                  99,  99,  99,  99,  99,  99,  99,  99)
                  }
ZIG_ZAG = ( 0,  1,  5,  6, 14, 15, 27, 28,
            2,  4,  7, 13, 16, 26, 29, 42,
            3,  8, 12, 17, 25, 30, 41, 43,
            9, 11, 18, 24, 31, 40, 44, 53,
           10, 19, 23, 32, 39, 45, 52, 54,
           20, 22, 33, 38, 46, 51, 55, 60,
           21, 34, 37, 47, 50, 56, 59, 61,
           35, 36, 48, 49, 57, 58, 62, 63)

HTABLE_DC0 = (0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01,
              0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # number of codes of each length 1..16 (12 total)
              0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, # symbols encoded (12)
              0x08, 0x09, 0x0a, 0x0b)

HTABLE_AC0 = (0x00, 0x02, 0x01, 0x03, 0x03, 0x02, 0x04, 0x03,
              0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7d, # - counts of codes of each length - 1..16 - total a2
              0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, # symbols encoded (0xa2)
              0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07,
              0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xa1, 0x08,
              0x23, 0x42, 0xb1, 0xc1, 0x15, 0x52, 0xd1, 0xf0,
              0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0a, 0x16,
              0x17, 0x18, 0x19, 0x1a, 0x25, 0x26, 0x27, 0x28,
              0x29, 0x2a, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
              0x3a, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
              0x4a, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
              0x5a, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
              0x6a, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79,
              0x7a, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
              0x8a, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98,
              0x99, 0x9a, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7,
              0xa8, 0xa9, 0xaa, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6,
              0xb7, 0xb8, 0xb9, 0xba, 0xc2, 0xc3, 0xc4, 0xc5,
              0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xd2, 0xd3, 0xd4,
              0xd5, 0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xe1, 0xe2,
              0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9, 0xea,
              0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8,
              0xf9, 0xfa)

HTABLE_DC1 = (0x00, 0x03, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
              0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
              0x08, 0x09, 0x0a, 0x0b)

HTABLE_AC1 = (0x00, 0x02, 0x01, 0x02, 0x04, 0x04, 0x03, 0x04,
              0x07, 0x05, 0x04, 0x04, 0x00, 0x01, 0x02, 0x77,
              0x00, 0x01, 0x02, 0x03, 0x11, 0x04, 0x05, 0x21,
              0x31, 0x06, 0x12, 0x41, 0x51, 0x07, 0x61, 0x71,
              0x13, 0x22, 0x32, 0x81, 0x08, 0x14, 0x42, 0x91,
              0xa1, 0xb1, 0xc1, 0x09, 0x23, 0x33, 0x52, 0xf0,
              0x15, 0x62, 0x72, 0xd1, 0x0a, 0x16, 0x24, 0x34,
              0xe1, 0x25, 0xf1, 0x17, 0x18, 0x19, 0x1a, 0x26,
              0x27, 0x28, 0x29, 0x2a, 0x35, 0x36, 0x37, 0x38,
              0x39, 0x3a, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48,
              0x49, 0x4a, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58,
              0x59, 0x5a, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68,
              0x69, 0x6a, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78,
              0x79, 0x7a, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87,
              0x88, 0x89, 0x8a, 0x92, 0x93, 0x94, 0x95, 0x96,
              0x97, 0x98, 0x99, 0x9a, 0xa2, 0xa3, 0xa4, 0xa5,
              0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xb2, 0xb3, 0xb4,
              0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xc2, 0xc3,
              0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xd2,
              0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0xd8, 0xd9, 0xda,
              0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9,
              0xea, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8,
              0xf9, 0xfa)

HEADER_HUFFMAN_TABLES = "header_huffman_tables"
DHT_DC0 = "dht_dc0"
DHT_AC0 = "dht_ac0"
DHT_DC1 = "dht_dc1"
DHT_AC1 = "dht_ac1"
DHTs= (DHT_DC0,DHT_AC0,DHT_DC1,DHT_AC1)
BITS =    "bits"
HUFFVAL = "huffval"
LENGTH =  "length"
VALUE =   "value"
FPGA_HUFFMAN_TABLE = "fpga_huffman_table"

class X393Jpeg(object):
    DRY_MODE= True # True
    DEBUG_MODE=1
    x393_mem=None
    x393_axi_tasks=None #x393X393AxiControlStatus
    x393_utils=None
    x393_cmprs_afi = None
    x393_sens_cmprs = None
    
    verbose=1
    def __init__(self, debug_mode=1,dry_mode=True, saveFileName=None):
        self.DEBUG_MODE=  debug_mode
        self.DRY_MODE=    dry_mode
        self.x393_mem=            X393Mem(debug_mode,dry_mode)
        
        self.x393_axi_tasks=      x393_axi_control_status.X393AxiControlStatus(debug_mode,dry_mode)
        self.x393_cmprs_afi =     x393_cmprs_afi.X393CmprsAfi(debug_mode,dry_mode)
        self.x393_utils=          x393_utils.X393Utils(debug_mode,dry_mode, saveFileName) # should not overwrite save file path
        self.x393_sens_cmprs =    x393_sens_cmprs.X393SensCmprs(debug_mode,dry_mode, saveFileName)

        try:
            self.verbose=vrlg.VERBOSE
        except:
            pass
        self.huff_tables=None

    def set_qtables(self,
                    chn,
                    index =     0, # index of a table pair
                    y_quality = 80,
                    c_quality = None,
                    portrait =  False,
                    verbose =   1
                    ):
        """
        Set a pair of quantization tables to FPGA
        @param chn - compressor channel number, "a" or "all" - same for all 4 channels
        @param y_quality - 1..100 - quantization quality for Y component
        @param c_quality - 1..100 - quantization quality for color components (None - use y_quality)
        @param portrait - False - use normal order, True - transpose for portrait mode images
        @param verbose - verbose level
        @return dictionary{"header","fpga"} each with a list of 2 lists of the 64 quantization
                table values [[y-table],[c-table]]
                'header' points to a pair of tables for the file header, 'fpga' - tables to be
                sent to the fpga 
        """
        try:
            if (chn == all) or (chn[0].upper() == "A"): #all is a built-in function
                for chn in range(4):
                    self.set_qtables (chn =       chn,
                                      index =     index,
                                      y_quality = y_quality,
                                      c_quality = c_quality,
                                      portrait =  portrait,
                                      verbose =   verbose)
                return
        except:
            pass
        quantization_data = self.get_qtables(y_quality = y_quality,
                                             c_quality = c_quality,
                                             portrait =  portrait,
                                             verbose = verbose - 1)
        quantization_data = quantization_data['fpga'][0] + quantization_data['fpga'][1]
        
        if verbose > 1:
            items_per_line = 8
            print("quantization_data:")
            for i, qd in enumerate(quantization_data):
                if (i % items_per_line) == 0:
                    print("%04x: "%(i), end = "")
                print ("%04x"%(qd), end = (", ","\n")[((i+1) % items_per_line) == 0])
        
        self.x393_sens_cmprs.program_quantization (chn =               chn,
                                                   index =             index,
                                                   quantization_data = quantization_data,
                                                   verbose =           verbose)

          
    def get_qtables(self,
                    y_quality = 80,
                    c_quality = None,
                    portrait = False,
                    verbose = 1
                    ):
        """
        Get a pair of quantization tables
        @param y_quality - 1..100 - quantization quality for Y component
        @param c_quality - 1..100 - quantization quality for color components (None - use y_quality)
        @param portrait - False - use normal order, True - transpose for portrait mode images
        @param verbose - verbose level
        @return dictionary{"header","fpga"} each with a list of 2 lists of the 64 quantization
                table values [[y-table],[c-table]]
                'header' points to a pair of tables for the file header, 'fpga' - tables to be
                sent to the fpga 
        """
        if (c_quality is None) or (c_quality == 0):
            c_quality = y_quality
        table_names = (("Y_landscape","C_landscape"),("Y_portrait","C_portrait"))[portrait]
        rslt = []
        fpga = []
        for quality, t_name in zip((int(y_quality),int(c_quality)),table_names):
            q = max(1,min(quality,100))
            if q <50:
                q = 5000 // q
            else:
                q = 200 - 2 * q
            tbl = [0]*64
            fpga_tbl = [0]*64
            for i,t in enumerate(STD_QUANT_TBLS[t_name]):
                d = max(1,min((t * q + 50) // 100, 255))
                tbl[ZIG_ZAG[i]] = d
#                fpga_tbl[i] = min(((0x20000 // d) + 1) >> 1, 0xffff)   
                fpga_tbl[ZIG_ZAG[i]] = min(((0x20000 // d) + 1) >> 1, 0xffff)   
            rslt.append(tbl)
            fpga.append(fpga_tbl)
        if verbose > 0:
            for n,title in enumerate(("Y","C")):
                print ("header %s table (%d):"%(title,n))
                for i, d in enumerate(rslt[n]):
                    print ("%3d, "%(d), end=("","\n")[((i+1) % 8) == 0])
            for n,title in enumerate(("Y","C")):
                print ("FPGA %s table:"%(title))
                for i, d in enumerate(fpga[n]):
                    print ("%04x, "%(d), end=("","\n")[((i+1) % 8) == 0])
        return ({"header":rslt,"fpga":fpga})
    
    def jpeg_htable_init(self,
                         verbose = 1):
        """
        Initialize Huffman tables data - both headres and FPGA
        """
        def make_header_ht(htable_dcac):
            return  {BITS:bytearray(htable_dcac[:16]),HUFFVAL:bytearray(list(htable_dcac[16:])+[0]*(256+16-len(htable_dcac)))}
           
        self.huff_tables={}
        self.huff_tables[HEADER_HUFFMAN_TABLES]=[]
        self.huff_tables[HEADER_HUFFMAN_TABLES].append(make_header_ht(HTABLE_DC0))
        self.huff_tables[HEADER_HUFFMAN_TABLES].append(make_header_ht(HTABLE_AC0))
        self.huff_tables[HEADER_HUFFMAN_TABLES].append(make_header_ht(HTABLE_DC1))
        self.huff_tables[HEADER_HUFFMAN_TABLES].append(make_header_ht(HTABLE_AC1))
        self.jpeg_htable_fpga_encode(verbose)
        if verbose > 1:
            for ntab in range(4):
                print ("header_huffman_tables[%d]"%(ntab))
                print ("bits[%d]:"%(ntab))
                for i,v in enumerate(self.huff_tables[HEADER_HUFFMAN_TABLES][ntab][BITS]):
                    print ("%02x"%(v), end = (" ","\n")[((i + 1) % 8) == 0])
                print ("huffval[%d]:"%(ntab))
                for i,v in enumerate(self.huff_tables[HEADER_HUFFMAN_TABLES][ntab][HUFFVAL]):
                    print ("%02x"%(v), end = (" ","\n")[((i + 1) % 8) == 0])
            for ntab in range(4):
                print ("%s: "%(DHTs[ntab]), end = " ")
                for v in self.huff_tables[DHTs[ntab]]:
                    print ("%02x"%(v), end = " ")
                print() 
                    
        return self.huff_tables

    def jpeg_htable_fpga_encode(self,
                                verbose = 1):
        """
        @brief encode all 4 Huffman tables into FPGA format
        additionally calculates number of symbols in each table
        
        @return OK - 0, -1 - too many symbols, -2 bad table, -3 - bad table number 
        """
        self.huff_tables[DHT_DC0] =  bytearray([0xff, 0xc4, 0x00, 0x00, 0x00])
        self.huff_tables[DHT_AC0] =  bytearray([0xff, 0xc4, 0x00, 0x00, 0x10])
        self.huff_tables[DHT_DC1] =  bytearray([0xff, 0xc4, 0x00, 0x00, 0x01])
        self.huff_tables[DHT_AC1] =  bytearray([0xff, 0xc4, 0x00, 0x00, 0x11])
        self.huff_tables[FPGA_HUFFMAN_TABLE] = [0] * 512 # unsigned long pga_huffman_table[512];
        for ntab in range(4):
            """
                codes: 256 elements of 
                struct huffman_fpga_code_t {
                  unsigned short value;       /// code value
                  unsigned short length;      /// code length
                };
            
            """
            codes = self.jpeg_prep_htable(self.huff_tables[HEADER_HUFFMAN_TABLES][ntab]) # may raise exception
            if verbose > 1:
                print ("codes[%d]"%ntab)
                for i,v in enumerate(codes):
                    print ("%08x"%(v[VALUE] | (v[LENGTH] << 16)), end = (" ","\n")[((i + 1) % 16) == 0])
                    
            if  ntab & 1:
                a = ((ntab & 2) << 7) # 0 256 0 256
                for i in range (0, 256, 16):
                    for j in range(15):
                        self.huff_tables[FPGA_HUFFMAN_TABLE][a + j] = codes[i + j][VALUE] | (codes[i + j][LENGTH] << 16) #a ll but DC column
                    a += 16
            else:
                a= ((ntab & 2) << 7) + 0x0f # in FPGA DC use spare parts of AC table
                for i in range(16):
                    self.huff_tables[FPGA_HUFFMAN_TABLE][a]= codes[i][VALUE] | (codes[i][LENGTH] << 16) # icodes[i];
                    a+=16;
            # Fill in the table headers:
            length = 19 #2 length bytes, 1 type byte, 16 lengths bytes
            for i in range(16): #(i=0; i<16; i++)
                # huff_tables.header_huffman_tables[ntab].bits[i]; /// first 16 bytes in each table number of symbols                
                length += self.huff_tables[HEADER_HUFFMAN_TABLES][ntab][BITS][i] # first 16 bytes in each table number of symbols
                # huff_tables.dht_all[(5*ntab)+2]=length >> 8;  /// high byte (usually 0)
                self.huff_tables[DHTs[ntab]][2] = length >> 8 # high byte (usually 0)
                # huff_tables.dht_all[(5*ntab)+3]=length& 0xff; /// low  byte
                self.huff_tables[DHTs[ntab]][3] = length & 0xff # low byte

        if verbose > 0:
            print("\nFPGA Huffman table\n")
            for i in range(512):
                print (" %06x"%(self.huff_tables[FPGA_HUFFMAN_TABLE][i]), end=("","\n")[((i+1) & 0x0f)==0])
        return self.huff_tables
        
    def jpeg_prep_htable (self,
                          htable):
        """
        /// Code below is based on jdhuff.c (from libjpeg)
        @brief Calculate huffman table (1 of 4) from the JPEG header to code lengh/value (for FPGA)
        @param htable bytearray() encoded Huffman table - 16 length bytes followed by up to 256 symbols
        @return hcodes combined (length<<16) | code table for each symbol
        Raises exceptions 
        """
        # Figure C.1: make table of Huffman code length for each symbol
        hcodes = [{LENGTH:0, VALUE:0} for _ in range (256)]
        p = 0
        for l in range (1,17):
            i = htable[BITS][l-1]
            if i < 0 or (p + i) > 256:
                raise Exception ("protect against table overrun")
    #    while (i--) hcodes[htable->huffval[p++]].length=l;
            for _ in range(i):
                hcodes[htable[HUFFVAL][p]][LENGTH] = l
                p = p + 1
        numsymbols = p
        # Figure C.2: generate the codes themselves
        # We also validate that the counts represent a legal Huffman code tree.
        code = 0
        si = hcodes[htable[HUFFVAL][0]][LENGTH]
        p = 0
        # htable->huffval[N] - N-th symbol value
        while p < numsymbols:
            if hcodes[htable[HUFFVAL][p]][LENGTH] < si:
                raise Exception ("Bad table/bug")
            while hcodes[htable[HUFFVAL][p]][LENGTH] == si:
                hcodes[htable[HUFFVAL][p]][VALUE] = code
                p = p + 1
                code = code + 1
            # code is now 1 more than the last code used for codelength si; but
            # it must still fit in si bits, since no code is allowed to be all ones.
            if  code >= (1 << si):
                raise Exception ("Bad code")
            code <<= 1
            si += 1
        return hcodes
    
    
    def jpegheader_create (self,
                           y_quality = 80,
                           c_quality = None,
                           portrait =  False,
                           height =    1936,
                           width =     2592,
                           color_mode = 0,
                           byrshift   = 0,
                           verbose    = 1):
        """
        Create JPEG file header
        @param y_quality - 1..100 - quantization quality for Y component
        @param c_quality - 1..100 - quantization quality for color components (None - use y_quality)
        @param portrait - False - use normal order, True - transpose for portrait mode images
        @param height - image height, pixels
        @param width - image width, pixels
        @param color_mode - one of the image formats (jpeg, jp4,)
        @param byrshift - Bayer shift
        @param verbose - verbose level
        """
        HEADER_YQTABLE =    0x19 # shift to Y q-table
        HEADER_CQTABLE_HD = 0x59 # shift to C q-table head?
        HEADER_CQTABLE =    0x5e # shift to C q-table
        HEADER_SOF =        0x9e #shift to start of frame
# first constant part of the header - 0x19 bytes
        JFIF1 = bytearray((0xff, 0xd8,                          # SOI start of image
                           0xff, 0xe0,                   # APP0
                           0x00, 0x10,                   # (16 bytes long)
                           0x4a, 0x46, 0x49, 0x46, 0x00, # JFIF null terminated
                           0x01, 0x01, 0x00, 0x00, 0x01,
                           0x00, 0x01, 0x00, 0x00,
                           0xff, 0xdb,                   # DQT (define quantization table)
                           0x00, 0x43,                   # 0x43 bytes long
                           0x00 ))

# second constant part of the header (starting from byte 0x59 - 0x5 bytes)
        JFIF2 = bytearray((0xff, 0xdb,                   # DQT (define quantization table)
                           0x00, 0x43,                   # 0x43 bytes long
                           0x01 ))                       # table number + (bytes-1)<<4 (0ne byte - 0, 2 bytes - 0x10)

        SOF_COLOR6 = bytearray((0x01, 0x22, 0x00, # id , freqx/freqy, q
                                0x02, 0x11, 0x01,
                                0x03, 0x11, 0x01))
        SOS_COLOR6 = bytearray((0x01, 0x00, # id, hufftable_dc/htable_ac
                                0x02, 0x11,
                                0x03, 0x11))

        SOF_JP46DC = bytearray((0x01, 0x11, 0x00, # id , freqx/freqy, q
                                0x02, 0x11, 0x00,
                                0x03, 0x11, 0x00,
                                0x04, 0x11, 0x00,
                                0x05, 0x11, 0x01,
                                0x06, 0x11, 0x01))
        SOS_JP46DC = bytearray((0x01, 0x00, # id, hufftable_dc/htable_ac
                                0x02, 0x00,
                                0x03, 0x00,
                                0x04, 0x00,
                                0x05, 0x11,
                                0x06, 0x11))

        SOF_MONO4 =  bytearray((0x01, 0x22, 0x00)) # id , freqx/freqy, q
        SOS_MONO4 =  bytearray((0x01, 0x00)) # id, hufftable_dc/htable_ac

        SOF_JP4 =    bytearray((0x04, 0x22, 0x00)) # id , freqx/freqy, q
        SOS_JP4 =    bytearray((0x04, 0x00)) # id, hufftable_dc/htable_ac

        SOF_JP4DC =  bytearray((0x04, 0x11, 0x00, # id , freqx/freqy, q
                                0x05, 0x11, 0x00,
                                0x06, 0x11, 0x00,
                                0x07, 0x11, 0x00))
        SOS_JP4DC =  bytearray((0x04, 0x00, # id, hufftable_dc/htable_ac
                                0x05, 0x00,
                                0x06, 0x00,
                                0x07, 0x00))

        SOF_JP4DIFF =bytearray((0x04, 0x11, 0x11, # will be adjusted to bayer shift, same for jp4hdr
                                0x05, 0x11, 0x11,
                                0x06, 0x11, 0x11,
                                0x07, 0x11, 0x11))
        SOS_JP4DIFF =bytearray((0x04, 0x11, # id, hufftable_dc/htable_ac
                                0x05, 0x11,
                                0x06, 0x11,
                                0x07, 0x11))
        def header_copy_sof( buf,
                             bpl,
                             bytes_sof):
            buf[bpl] = len(bytes_sof) + 8
            buf.append(len(bytes_sof) // 3)
            buf += bytes_sof
        def header_copy_sos( buf,
                             bytes_sos):
            buf.append(len(bytes_sos) + 6)
            buf.append(len(bytes_sos) // 2)
            buf += bytes_sos
            
        self.jpeg_htable_init(verbose)
        
#  memcpy((void *) &buf[0],                 (void *) jfif1, sizeof (jfif1)); /// including DQT0 header
        buf = bytearray(JFIF1)                        # including DQT0 header
##  memcpy((void *) &buf[header_cqtable_hd], (void *) jfif2, sizeof (jfif2)); /// DQT1 header
        qtables=self.get_qtables(y_quality = y_quality,
                                 c_quality = c_quality,
                                 portrait =  portrait,
                                 verbose =   verbose )
        """
        rslt=get_qtable(params->quality2, &buf[header_yqtable], &buf[header_cqtable]); /// will copy both quantization tables
        @return dictionary{"header","fpga"} each with a list of 2 lists of the 64 quantization
                table values [[y-table],[c-table]]
                'header' points to a pair of tables for the file header, 'fpga' - tables to be
                sent to the fpga 
        
        """
        if verbose > 0:
            header_yqtable = len(buf) 
            print ("header_yqtable = 0x%x (==0x%x)"%(header_yqtable,HEADER_YQTABLE))
        buf += bytearray(qtables["header"][0]) # 0x19..0x58
        if verbose > 0:
            header_cqtable_hd = len(buf) 
            print ("header_cqtable_hd = 0x%x (==0x%x)"%(header_cqtable_hd,HEADER_CQTABLE_HD))
        buf += bytearray(JFIF2)              # 0x55..0x5d # DQT1 header
        if verbose > 0:
            header_cqtable = len(buf) 
            print ("header_cqtable = 0x%x (==0x%x)"%(header_cqtable,HEADER_CQTABLE))
        buf += bytearray(qtables["header"][1]) # 0x5e..0x9d
        header_sof = len(buf)
        if verbose > 0:
            print ("header_sof = 0x%x (==0x%x)"%(header_sof,HEADER_SOF))
        # bp is header_sof now
        buf += bytearray((0xff,0xc0))        # 0x9e..0x9f
        buf.append(0)                        # 0xa0  high byte length - always 0
        bpl = len(buf)                       # save pointer to length (low byte) 0x61
        buf.append(0)                        # 0xa1  length low byte will be here
        buf.append(0x8)                      # 0xa2  8bpp
        buf.append(height >> 8)              # 0xa3  height MSB
        buf.append(height & 0xff)            # 0xa4  height LSB
        buf.append(width >> 8)               # 0xa5  width MSB
        buf.append(width & 0xff)             # 0xa6  width LSB
# copy SOF0 (constants combined with bayer shift for jp4diff/jp4hdr)
        if color_mode in (vrlg.CMPRS_CBIT_CMODE_JPEG18,  # color, 4:2:0, 18x18(old)
                          vrlg.CMPRS_CBIT_CMODE_MONO6,   # monochrome, (4:2:0)
                          vrlg.CMPRS_CBIT_CMODE_JPEG20,  # color, 4:2:0, 20x20, middle of the tile (not yet implemented)
                          vrlg.CMPRS_CBIT_CMODE_JP46):   # jp4, original (4:2:0)
            header_copy_sof(buf, bpl, SOF_COLOR6)
        elif color_mode == vrlg.CMPRS_CBIT_CMODE_MONO4:  #  monochrome, 4 blocks (but still with 2x2 macroblocks)
            header_copy_sof(buf, bpl, SOF_MONO4)
        elif color_mode == vrlg.CMPRS_CBIT_CMODE_JP4:    # jp4, 4 blocks
            header_copy_sof(buf, bpl, SOF_JP4)
        elif color_mode == vrlg.CMPRS_CBIT_CMODE_JP46DC: # jp4, dc -improved (4:2:0)
            header_copy_sof(buf, bpl, SOF_JP46DC)
        elif color_mode == vrlg.CMPRS_CBIT_CMODE_JP4DC:  # jp4, 4 blocks, dc -improved
            header_copy_sof(buf, bpl, SOF_JP4DC)
        elif color_mode in (vrlg.CMPRS_CBIT_CMODE_JP4DIFF, # jp4, 4 blocks, differential red := (R-G1), blue:=(B-G1), green=G1, green2 (G2-G1). G1 is defined by Bayer shift, any pixel can
                            vrlg.CMPRS_CBIT_CMODE_JP4DIFFDIV2): # jp4, 4 blocks, differential, divide differences by 2: red := (R-G1)/2, blue:=(B-G1)/2, green=G1, green2 (G2-G1)/2
            header_copy_sof(buf, bpl, SOF_JP4DIFF)
            buf[header_sof + 12 + 3 * ((4-byrshift) & 3)]=0 # set quantization table 0 for the base color
        elif color_mode in (vrlg.CMPRS_CBIT_CMODE_JP4DIFFHDR, # jp4, 4 blocks, differential HDR: red := (R-G1), blue:=(B-G1), green=G1, green2 (high gain)=G2) (G1 and G2 - diagonally opposite)
                            vrlg.CMPRS_CBIT_CMODE_JP4DIFFHDRDIV2): # jp4, 4 blocks, differential HDR: red := (R-G1)/2, blue:=(B-G1)/2, green=G1, green2 (high gain)=G2)
            header_copy_sof(buf, bpl, SOF_JP4DIFF)
            buf[header_sof + 12 + 3 * ((4 - byrshift) & 3)]=0 # set quantization table 0 for the base color
            buf[header_sof + 12 + 3 * ((6 - byrshift) & 3)]=0 # set quantization table 0 for the HDR color
# Include 4 Huffman tables
        for ntab in range(4):
            buf += self.huff_tables[DHTs[ntab]]
            length=  (self.huff_tables[DHTs[ntab]][2]<<8)+self.huff_tables[DHTs[ntab]][3]-3;  # table length itself, excluding 2 length bytes and type byte
            buf += self.huff_tables[HEADER_HUFFMAN_TABLES][ntab][BITS]
            buf += self.huff_tables[HEADER_HUFFMAN_TABLES][ntab][HUFFVAL][:length-16]

        # copy SOS0 (constants combined with bayer shift for jp4diff/jp4hdr)
        header_sos = len(buf)
        buf += bytearray((0xff,0xda)) # SOS tag
        buf.append(0);                # high byte length - always 0
        if color_mode in (vrlg.CMPRS_CBIT_CMODE_JPEG18,  # color, 4:2:0, 18x18(old)
                          vrlg.CMPRS_CBIT_CMODE_MONO6,   # monochrome, (4:2:0)
                          vrlg.CMPRS_CBIT_CMODE_JPEG20,  # color, 4:2:0, 20x20, middle of the tile (not yet implemented)
                          vrlg.CMPRS_CBIT_CMODE_JP46):   # jp4, original (4:2:0)
            header_copy_sos(buf, SOS_COLOR6)
        elif color_mode == vrlg.CMPRS_CBIT_CMODE_MONO4:  #  monochrome, 4 blocks (but still with 2x2 macroblocks)
            header_copy_sos(buf, SOS_MONO4)
        elif color_mode == vrlg.CMPRS_CBIT_CMODE_JP4:    # jp4, 4 blocks
            header_copy_sos(buf, SOS_JP4)
        elif color_mode == vrlg.CMPRS_CBIT_CMODE_JP46DC: # jp4, dc -improved (4:2:0)
            header_copy_sos(buf, SOS_JP46DC)
        elif color_mode == vrlg.CMPRS_CBIT_CMODE_JP4DC:  # jp4, 4 blocks, dc -improved
            header_copy_sos(buf, SOS_JP4DC)

        elif color_mode in (vrlg.CMPRS_CBIT_CMODE_JP4DIFF, # jp4, 4 blocks, differential red := (R-G1), blue:=(B-G1), green=G1, green2 (G2-G1). G1 is defined by Bayer shift, any pixel can
                            vrlg.CMPRS_CBIT_CMODE_JP4DIFFDIV2): # jp4, 4 blocks, differential, divide differences by 2: red := (R-G1)/2, blue:=(B-G1)/2, green=G1, green2 (G2-G1)/2
            header_copy_sos(buf, SOS_JP4DIFF)
            buf[header_sos + 6 + 2 * ((4-byrshift) & 3)]=0 # set huffman table 0 for the base color
        elif color_mode in (vrlg.CMPRS_CBIT_CMODE_JP4DIFFHDR, # jp4, 4 blocks, differential HDR: red := (R-G1), blue:=(B-G1), green=G1, green2 (high gain)=G2) (G1 and G2 - diagonally opposite)
                            vrlg.CMPRS_CBIT_CMODE_JP4DIFFHDRDIV2): # jp4, 4 blocks, differential HDR: red := (R-G1)/2, blue:=(B-G1)/2, green=G1, green2 (high gain)=G2)
            header_copy_sof(buf, bpl, SOF_JP4DIFF)
            buf[header_sos + 6 + 2 * ((4 - byrshift) & 3)]=0 # set huffman table 0  for the base color
            buf[header_sos + 6 + 2 * ((6 - byrshift) & 3)]=0 # set huffman table 0 for the HDR color
        buf.append(0x00) # Spectral selection start
        buf.append(0x3f) # Spectral selection end
        buf.append(0x00) # Successive approximation (2 values 0..13)
        if verbose > 0:
            print("JPEG header length=%d"%(len(buf)))
            for i, d in enumerate(buf):
                if (i % 16) == 0:
                    print("%03x:"%(i), end = "")
                print(" %02x"%(d), end = ("","\n")[((i + 1) % 16) == 0])
            buf353=self.jpeg_header_353()
            print()
            print("Comparing with 353 JPEG header")
            diffs = 0
            for i, p in enumerate(zip(buf,buf353)):
                if (i % 32) == 0:
                    print("%03x:"%(i), end = "")
                print(" %1s"%((".","X")[p[0] != p[1]]), end = ("","\n")[((i + 1) % 32) == 0])
                if p[0] != p[1]:
                    diffs += 1
            print("\nNumber of bytes that differ = %d"%(diffs))    
        return {"header":buf,
                "quantization":qtables["fpga"],
                "huffman":  self.huff_tables[FPGA_HUFFMAN_TABLE]}
    def jpeg_write(self,
                   file_path = "img.jpeg", 
                   channel =   0, 
                   y_quality = 100, #80,
                   c_quality = None,
                   portrait =  False,
                   color_mode = 0,
                   byrshift   = 0,
                   server_root = "/www/pages/",
                   verbose    = 1):
        """
        Create JPEG image from the latest acquired in the camera
        @param file_path - camera file system path (starts with "/") or relative to web server root 
        @param channel -   compressor channel
        @param y_quality - 1..100 - quantization quality for Y component
        @param c_quality - 1..100 - quantization quality for color components (None - use y_quality)
        @param portrait - False - use normal order, True - transpose for portrait mode images
        @param color_mode - one of the image formats (jpeg, jp4,)
        @param byrshift - Bayer shift
        @param server_root - files ystem path to the web server root directory
        @param verbose - verbose level
        """
        allFiles = False
        if file_path[0] == "/":
            server_root = "" # just do not add anything 
        try:
            if (channel == all) or (channel[0].upper() == "A"): #all is a built-in function
                allFiles = True
        except:
            pass
        if allFiles:        
            html_text = """
<html>
  <head>
    <title></title>
    <meta content="">
    <style>
      table { border-collapse: collapse;}
      table td, table th {padding: 0;}
    </style>
  </head>
  <body>
     <table> 
       <tr>"""
            html_text_td = """
         <td><a href="%s"><img src="%s" style="image-orientation: 270deg; width:100%%; height:auto;" /></a></td>"""
            html_text_finish = """
       </tr>
     </table>
  </body>
</html>"""
                
            for channel in (3,2,0,1): #range(4):
                file_path_mod = file_path.replace(".","_%d."%channel)
                if verbose > 1:
                    print(html_text_td)
                html_text += html_text_td%(file_path_mod,file_path_mod) 
                self.jpeg_write (file_path = file_path_mod, 
                                 channel =   channel, 
                                 y_quality = y_quality, #80,
                                 c_quality = c_quality,
                                 portrait =  portrait,
                                 color_mode = color_mode,
                                 byrshift   = byrshift,
                                 verbose    = verbose)
            html_text += html_text_finish
            if server_root:
                dotpos = file_path.rfind(".")
                if dotpos <0:
                    html_name = file_path + ".html"
                else:     
                    html_name = file_path[:dotpos] + ".html"
                if verbose > 1:
                    print ("path = ",server_root+html_name)
                    print ("text = ",html_text)    
                with open (server_root+html_name, "w+b") as bf:
                    bf.write(html_text)
            return
        
        jpeg_data = self.jpegheader_create (
                           y_quality = y_quality,
                           c_quality = c_quality,
                           portrait =  portrait,
                           height =    x393_sens_cmprs.GLBL_WINDOW["height"] & 0xfff0,
                           width =     x393_sens_cmprs.GLBL_WINDOW["width"] & 0xfff0,
                           color_mode = color_mode,
                           byrshift   = byrshift,
                           verbose    = verbose - 1)
        meta = self.x393_cmprs_afi.afi_mux_get_image_meta(
                          port_afi =     0,
                          channel =      channel,
                          cirbuf_start = x393_sens_cmprs.GLBL_CIRCBUF_STARTS[channel],
                          circbuf_len =  x393_sens_cmprs.GLBL_CIRCBUF_CHN_SIZE,
                          verbose = 1)
        print ("meta = ",meta)
        for s in meta["segments"]:
            print ("start_address = 0x%x, length = 0x%x"%(s[0],s[1]))
        with open (server_root+file_path, "w+b") as bf:
            bf.write(jpeg_data["header"])
            for s in meta["segments"]:
                print ("start_address = 0x%x, length = 0x%x"%(s[0],s[1]))
                self.x393_mem._mem_write_to_file (bf =         bf,
                                                  start_addr = s[0],
                                                  length =     s[1])
            bf.write(bytearray((0xff,0xd9)))
                
        
        
        
    def jpegheader_write  (self,
                           file_path = "jpeg", 
                           y_quality = 80,
                           c_quality = None,
                           portrait =  False,
                           height =    1936,
                           width =     2592,
                           color_mode = 0,
                           byrshift   = 0,
                           verbose    = 1):
        """
        Create JPEG file header and trailer
        @param file_path - file system path (will create two files *.head and *.tail
        @param y_quality - 1..100 - quantization quality for Y component
        @param c_quality - 1..100 - quantization quality for color components (None - use y_quality)
        @param portrait - False - use normal order, True - transpose for portrait mode images
        @param height - image height, pixels
        @param width - image width, pixels
        @param color_mode - one of the image formats (jpeg, jp4,)
        @param byrshift - Bayer shift
        @param verbose - verbose level
        """
        jpeg_data = self.jpegheader_create (
                           y_quality = y_quality,
                           c_quality = c_quality,
                           portrait =  portrait,
                           height =    height,
                           width =     width,
                           color_mode = color_mode,
                           byrshift   = byrshift,
                           verbose    = verbose - 1)

        with open(file_path+".head", "w+b") as sf:
            sf.write(jpeg_data["header"])
        with open(file_path+".tail", "w+b") as sf:
            sf.write(bytearray((0xff,0xd9)))
          
    def jpeg_header_353 (self):
        return bytearray((
 0xfe, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
 0x00, 0x01, 0x00, 0x00, 0xff, 0xdb, 0x00, 0x43, 0x00, 0x06, 0x04, 0x05, 0x06, 0x05, 0x04, 0x06,
 0x06, 0x05, 0x06, 0x07, 0x07, 0x06, 0x08, 0x0a, 0x10, 0x0a, 0x0a, 0x09, 0x09, 0x0a, 0x14, 0x0e,
 0x0f, 0x0c, 0x10, 0x17, 0x14, 0x18, 0x18, 0x17, 0x14, 0x16, 0x16, 0x1a, 0x1d, 0x25, 0x1f, 0x1a,
 0x1b, 0x23, 0x1c, 0x16, 0x16, 0x20, 0x2c, 0x20, 0x23, 0x26, 0x27, 0x29, 0x2a, 0x29, 0x19, 0x1f,
 0x2d, 0x30, 0x2d, 0x28, 0x30, 0x25, 0x28, 0x29, 0x28, 0xff, 0xdb, 0x00, 0x43, 0x01, 0x07, 0x07,
 0x07, 0x0a, 0x08, 0x0a, 0x13, 0x0a, 0x0a, 0x13, 0x28, 0x1a, 0x16, 0x1a, 0x28, 0x28, 0x28, 0x28,
 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28,
 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28,
 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0xff, 0xc0,
 0x00, 0x11, 0x08, 0x07, 0x90, 0x0a, 0x20, 0x03, 0x01, 0x22, 0x00, 0x02, 0x11, 0x01, 0x03, 0x11,
 0x01, 0xff, 0xc4, 0x00, 0x1f, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00,
 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09,
 0x0a, 0x0b, 0xff, 0xc4, 0x00, 0xb5, 0x10, 0x00, 0x02, 0x01, 0x03, 0x03, 0x02, 0x04, 0x03, 0x05,
 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7d, 0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21,
 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xa1, 0x08, 0x23,
 0x42, 0xb1, 0xc1, 0x15, 0x52, 0xd1, 0xf0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0a, 0x16, 0x17,
 0x18, 0x19, 0x1a, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2a, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a,
 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4a, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5a,
 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6a, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7a,
 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99,
 0x9a, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7,
 0xb8, 0xb9, 0xba, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xd2, 0xd3, 0xd4, 0xd5,
 0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9, 0xea, 0xf1,
 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9, 0xfa, 0xff, 0xc4, 0x00, 0x1f, 0x01, 0x00, 0x03,
 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,
 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0xff, 0xc4, 0x00, 0xb5, 0x11, 0x00,
 0x02, 0x01, 0x02, 0x04, 0x04, 0x03, 0x04, 0x07, 0x05, 0x04, 0x04, 0x00, 0x01, 0x02, 0x77, 0x00,
 0x01, 0x02, 0x03, 0x11, 0x04, 0x05, 0x21, 0x31, 0x06, 0x12, 0x41, 0x51, 0x07, 0x61, 0x71, 0x13,
 0x22, 0x32, 0x81, 0x08, 0x14, 0x42, 0x91, 0xa1, 0xb1, 0xc1, 0x09, 0x23, 0x33, 0x52, 0xf0, 0x15,
 0x62, 0x72, 0xd1, 0x0a, 0x16, 0x24, 0x34, 0xe1, 0x25, 0xf1, 0x17, 0x18, 0x19, 0x1a, 0x26, 0x27,
 0x28, 0x29, 0x2a, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
 0x4a, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5a, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
 0x6a, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7a, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88,
 0x89, 0x8a, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6,
 0xa7, 0xa8, 0xa9, 0xaa, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xc2, 0xc3, 0xc4,
 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xe2,
 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9, 0xea, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9,
 0xfa, 0xff, 0xda, 0x00, 0x0c, 0x03, 0x01, 0x00, 0x02, 0x11, 0x03, 0x11, 0x00, 0x3f, 0x00))

"""
ff d9
"""        
"""
Camera compressors testing sequence
cd /usr/local/verilog/; test_mcntrl.py @hargs
#or (for debug)
cd /usr/local/verilog/; test_mcntrl.py @hargs -x -v

Next 2 lines needed to use jpeg functionality if the program was started w/o setup_all_sensors True None 0xf
specify_phys_memory
specify_window

# Initialize memory with current calibration.
measure_all "*DI"
# Run 'measure_all' again (but w/o arguments) to perform full calibration (~10 minutes) and save results.
# Needed after new bitstream
# setup_all_sensors , 3-rd argument - bitmask of sensors to initialize
setup_all_sensors True None 0xf

#reset all compressors - NOT NEEDED
#compressor_control all 0

#next line to make compressor aways use the same input video frame buffer (default - 2 ping-pong frame buffers)
#axi_write_single_w 0x6c4 0
#set quadrants
#set_sensor_io_ctl 0 None None None None None 0 0x4
set_sensor_io_ctl 0 None None None None None 0 0xe
set_sensor_io_ctl 1 None None None None None 0 0xe
set_sensor_io_ctl 2 None None None None None 0 0x4
set_sensor_io_ctl 3 None None None None None 0 0xe

# Set Bayer = 3 (probably #1 and #3 need different hact/pxd delays to use the same compressor bayer for all channels)
compressor_control  all  None  None  None None None  3

#Gamma 0.57
program_gamma all 0 0.57 0.04
program_gamma all 0 1.0 0.04
#colors - outdoor
write_sensor_i2c  all 1 0 0x9035000a
write_sensor_i2c  all 1 0 0x902c000e
write_sensor_i2c  all 1 0 0x902d000d

#colors indoor
write_sensor_i2c  all 1 0 0x90350009
write_sensor_i2c  all 1 0 0x902c000f
write_sensor_i2c  all 1 0 0x902d000a

#exposure 0x100 lines (default was 0x797)
write_sensor_i2c  all 1 0 0x90090100

#exposure 0x200 lines (default was 0x797)
write_sensor_i2c  all 1 0 0x90090200

#exposure 0x400 lines (default was 0x797)
write_sensor_i2c  all 1 0 0x90090400

#exposure 0x500 lines (default was 0x797)
write_sensor_i2c  all 1 0 0x90090500

#exposure 0x797 (default)
write_sensor_i2c  all 1 0 0x90090797


#Get rid of the corrupted last pixel column
#longer line (default 0xa1f)
write_sensor_i2c  all 1 0 0x90040a23

#increase scanline write (memory controller) width in 16-bursts (was 0xa2)
axi_write_single_w 0x696 0x079800a3
axi_write_single_w 0x686 0x079800a3
axi_write_single_w 0x6a6 0x079800a3
axi_write_single_w 0x6b6 0x079800a3

#color pattern:
#turn off black shift (normally 0xa8)
write_sensor_i2c  all 1 0 0x90490000
 
write_sensor_i2c  all 1 0 0x90a00001
write_sensor_i2c  all 1 0 0x90a00009
write_sensor_i2c  all 1 0 0x90a00019
#running 1:
write_sensor_i2c  all 1 0 0x90a00029
...
write_sensor_i2c  all 1 0 0x90a00041

#color pattern off: 
write_sensor_i2c  all 1 0 0x90a00000



#run compressors once (#1 - stop gracefully, 0 - reset, 2 - single, 3 - repetitive with sync to sensors)
compressor_control all 2

jpeg_write  "img.jpeg" all


#changing quality (example 85%):
set_qtables all 0 85
compressor_control all 2
jpeg_write  "img.jpeg" all 85

-----
#turn off black shift (normally 0xa8)
write_sensor_i2c  all 1 0 0x90490000
program_gamma all 0 1.0 0.00                                       
membridge_start                                                      
mem_dump 0x2ba00000 0x100                                            
mem_save "/usr/local/verilog/sensor_dump_01" 0x2ba00000 0x2300000
#scp -p root@192.168.0.8:/mnt/mmc/local/verilog/sensor_dump_01 /home/andrey/git/x393/py393/dbg1


setup_membridge_sensor  <write_mem=False>  <cache_mode=3>  <window_width=2592>  <window_height=1944>  <window_left=0>  <window_top=0>  <membridge_start=731906048>  <membridge_end=768606208>  <verbose=1> 
setup_membridge_sensor  0  3  2608  1936 
setup_membridge_sensor  <num_sensor=0>  <write_mem=False>  <cache_mode=3>  <window_width=2592>  <window_height=1944>  <window_left=0>  <window_top=0>  <last_buf_frame=1>  <membridge_start=731906048>  <membridge_end=768606208>  <verbose=1> 
setup_membridge_sensor  0 0  3  2608  1936 
setup_membridge_sensor  1 0  3  2608  1936 

# Trying quadrants @param quadrants -  90-degree shifts for data [1:0], hact [3:2] and vact [5:4] (6'h01), None - no change
# set_sensor_io_ctl  <num_sensor>  <mrst=None>  <arst=None>  <aro=None>  <mmcm_rst=None>  <clk_sel=None>  <set_delays=False>  <quadrants=None> 

set_sensor_io_ctl 0 None None None None None 0 1 
set_sensor_io_ctl 1 None None None None None 0 1

#make all reddish
write_sensor_i2c  0 1 0 0x90350008
write_sensor_i2c  0 1 0 0x902c0008
write_sensor_i2c  0 1 0 0x902d001f

write_sensor_i2c  1 1 0 0x90350008
write_sensor_i2c  1 1 0 0x902c0008
write_sensor_i2c  1 1 0 0x902d001f

write_sensor_i2c  2 1 0 0x90350008
write_sensor_i2c  2 1 0 0x902c0008
write_sensor_i2c  2 1 0 0x902d001f

write_sensor_i2c  3 1 0 0x90350008
write_sensor_i2c  3 1 0 0x902c0008
write_sensor_i2c  3 1 0 0x902d001f

print_debug 0x35 ox66

set_qtables all 0 90
jpeg_write  "/www/pages/img.jpeg" all
compressor_control  all  None  1
compressor_control  all  None  0

mem_save "/usr/local/verilog/memdump_chn0" 0x27a00000 0x01001000

write_sensor_i2c  0 1 0 0x91900004
read_sensor_i2c 0
print_sensor_i2c 0 

set_sensor_i2c_table_reg_wr  0 0x00 0x48 3 100 1
set_sensor_i2c_table_reg_wr  0 0x90 0x48 3 100 1
set_sensor_i2c_table_reg_rd  0 0x01 0 2 100 1
set_sensor_i2c_table_reg_rd  0 0x91 0 2 100 1

========
cd /usr/local/verilog/; test_mcntrl.py @hargs
measure_all "*DI"
setup_all_sensors True None 0xf
set_sensor_io_ctl 0 None None None None None 0 0x4
set_sensor_io_ctl 1 None None None None None 0 0xe
set_sensor_io_ctl 2 None None None None None 0 0x4
set_sensor_io_ctl 3 None None None None None 0 0xe
compressor_control  all  None  None  None None None  3
program_gamma all 0 0.57 0.04
write_sensor_i2c  all 1 0 0x90350009
write_sensor_i2c  all 1 0 0x902c000f
write_sensor_i2c  all 1 0 0x902d000a
write_sensor_i2c  all 1 0 0x90040a23
axi_write_single_w 0x696 0x079800a3
axi_write_single_w 0x686 0x079800a3
axi_write_single_w 0x6a6 0x079800a3
axi_write_single_w 0x6b6 0x079800a3

compressor_control all 2

jpeg_write  "img.jpeg" all


write_sensor_i2c  0 1 0 0x91900004
print_sensor_i2c 0 


#r
add hwmon:
root@elphel393:/sys/devices/amba.0/f8007100.ps7-xadc# cat /sys/devices/amba.0/f8007100.ps7-xadc/temp
47
root@elphel393:/sys/devices/amba.0/f8007100.ps7-xadc# cat /sys/devices/amba.0/f8007100.ps7-xadc/temp_max
48
root@elphel393:/sys/devices/amba.0/f8007100.ps7-xadc# cat /sys/devices/amba.0/f8007100.ps7-xadc/temp_min
41
root@elphel393:/sys/devices/amba.0/f8007100.ps7-xadc# cat /sys/devices/amba.0/f8007100.ps7-xadc/v
0
root@elphel393:/sys/devices/amba.0/f8007100.ps7-xadc# cat /sys/devices/amba.0/f8007100.ps7-xadc/vccaux
1808
root@elphel393:/sys/devices/amba.0/f8007100.ps7-xadc# cat /sys/devices/amba.0/f8007100.ps7-xadc/vccbram
967
root@elphel393:/sys/devices/amba.0/f8007100.ps7-xadc# cat /sys/devices/amba.0/f8007100.ps7-xadc/vccint
966


"""
