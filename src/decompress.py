#!/usr/bin/python

import struct
import sys
import os

class ImageDecompressor(object):

    _file = None

    def __init__(self, file_name):
        self._file = open(file_name, 'rb')

    def __del__(self):
        if self._file != None:
            self._file.close()

    def get_bytes(self):
        out_bytes = ''
        out_offset = 0

        while True:
            in_preamble_len = 9
            in_bytes = self._file.read(in_preamble_len)
            (in_unknown, in_block_len, out_block_len) = struct.unpack('<BII', in_bytes)

            if in_unknown != 0x03:
                return out_bytes

            in_body_len = in_block_len - in_preamble_len
            in_bytes += self._file.read(in_body_len)
            in_offset = in_preamble_len

            control_bits = 0x00000001
            while in_offset < in_block_len:
                if control_bits == 0x00000001:
                    (control_bits,) = struct.unpack('<I', in_bytes[in_offset:in_offset + 4])
                    control_bits |= 0x80000000
                    in_offset += 4

                print '--> In: 0x%x Out: 0x%x Control: 0x%8x' % (in_offset, out_offset, control_bits)

                emit_single_byte = ~control_bits & 0x00000001
                control_bits >>= 1

                if emit_single_byte:
                    out_byte = in_bytes[in_offset]
                    in_offset += 1

                    out_bytes += out_byte
                    out_offset += 1

                else:
                    (first_byte,) = struct.unpack('<B', in_bytes[in_offset])
                    operation = first_byte & 0x0F

                    print '  --> op_nimble 0x%01x / op_byte 0x%02x' % (operation, first_byte)

                    if (operation & 0x0F) == 0x0F:
                        (segment_len, out_byte) = struct.unpack('<BB', in_bytes[in_offset + 1:in_offset + 3])
                        out_byte = chr(out_byte)
                        segment_len = segment_len << 4 | first_byte >> 4
                        in_offset += 3

                        if segment_len == 0:
                            (segment_len,) = struct.unpack('<I', in_bytes[in_offset:in_offset + 4])
                            in_offset += 4

                        out_bytes += ''.join(out_byte for _ in range(segment_len))
                        out_offset += segment_len

                    else:
                        if (operation & 0x0F) == 0x07:
                            (segment_len, out_relative_start_offset) = struct.unpack('<BH', in_bytes[in_offset + 1:in_offset + 4])
                            out_relative_start_offset = out_relative_start_offset << 1 | segment_len >> 7
                            out_relative_stop_offset = 3
                            segment_len = (segment_len & 0x7F) << 4 | first_byte >> 4
                            in_offset += 4

                        elif (operation & 0x07) == 0x03:
                            (out_relative_start_offset,) = struct.unpack('<H', in_bytes[in_offset + 1:in_offset + 3])
                            out_relative_stop_offset = 3
                            segment_len = (first_byte >> 3)
                            in_offset += 3

                        elif (operation & 0x03) == 0x02:
                            (out_relative_start_offset,) = struct.unpack('<B', in_bytes[in_offset + 1:in_offset + 2])
                            out_relative_start_offset = out_relative_start_offset << 2 | first_byte >> 6
                            out_relative_stop_offset = 3
                            segment_len = (first_byte >> 2) & 0x0F
                            in_offset += 2

                        elif (operation & 0x03) == 0x01:
                            (out_relative_start_offset,) = struct.unpack('<B', in_bytes[in_offset + 1:in_offset + 2])
                            out_relative_start_offset = out_relative_start_offset << 6 | first_byte >> 2
                            out_relative_stop_offset = 3
                            segment_len = 0
                            in_offset += 2

                        elif (operation & 0x03) == 0x00:
                            out_relative_start_offset = first_byte >> 2
                            out_relative_stop_offset = 3
                            segment_len = 0
                            in_offset += 1

                        out_current_offset = out_offset - out_relative_start_offset
                        out_stop_offset = out_current_offset + out_relative_stop_offset + segment_len - 1
                        while out_current_offset <= out_stop_offset:
                            out_bytes += out_bytes[out_current_offset]
                            out_current_offset += 1
                            out_offset += 1

        return out_bytes

if __name__ == '__main__':

    if len(sys.argv) != 3:
        print 'Usage:'
        print '\tpython decompress.py <input_file.mrimg> <output_file.bin>'

    try:
        out_file = open(sys.argv[2], 'wb')
        
        decompressor = ImageDecompressor(sys.argv[1])
    
        out_bytes = decompressor.get_bytes()
        out_file.write(out_bytes)
        
    finally:
        out_file.close()