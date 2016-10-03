#!/usr/bin/python

import sys


class ImageDecompressor(object):

    IMAGE_PREAMBLE_LEN = 9

    _file = None

    def __init__(self, file_name):
        self._file = open(file_name, 'rb')

    def __del__(self):
        if self._file is not None:
            self._file.close()

    def get_bytes(self):

        block_num = 0
        out_bytes = ''

        def extract_dword(block, offset):
            return block[offset + 3] << 24 | block[offset + 2] << 16 | block[offset + 1] << 8 | block[offset]

        def extract_bits(value, first, count):
            return ((value & (1 << (first + count)) - 1)) >> first

        while True:
            in_block = bytearray(self._file.read(self.IMAGE_PREAMBLE_LEN))
            in_preamble_flags = in_block[0]
            in_block_len = extract_dword(in_block, 1)
            out_block_expected_len = extract_dword(in_block, 5)

            # An .mrimg file includes a trailer with metadata about the
            # image such as the offset where the imaged data ends.  Ultimately
            # this code needs to be made of this metadata such that it
            # reliably knows when to stop decompressing image data.  In the
            # mean time, the following check is sufficient for determining
            # that the next chunk of data does not include a valid block
            # preamble.  This indicates that no more image data is available
            # and that decompression is complete.
            if in_preamble_flags != 0x03:
                return out_bytes

            in_block_remaining_bytes_len = in_block_len - self.IMAGE_PREAMBLE_LEN
            in_block += bytearray(self._file.read(in_block_remaining_bytes_len))
            in_block_offset = self.IMAGE_PREAMBLE_LEN

            out_block = bytearray(out_block_expected_len)
            out_block_offset = 0

            control_flags = 0x00000001
            while in_block_offset < in_block_len:
                if control_flags == 0x00000001:
                    control_flags = extract_dword(in_block, in_block_offset)
                    control_flags |= 0x80000000
                    in_block_offset += 4
                    continue

                print '--> Block: %4d\tIn Offset: 0x%8x\tOut Offset: 0x%8x\tFlags: 0x%8x' % (block_num, in_block_offset, out_block_offset, control_flags)

                is_literal = not control_flags & 0x00000001
                if is_literal:
                    print '  --> Literal \'%c\' (0x%02x)' % (in_block[in_block_offset], in_block[in_block_offset])

                    out_byte = in_block[in_block_offset]
                    out_block[out_block_offset] = out_byte
                    in_bytes_consumed = 1
                    out_bytes_emitted = 1

                else:
                    print '  --> Operation Nibble 0x%01x' % (extract_bits(extract_dword(in_block, in_block_offset), 0, 4))

                    in_bytes = extract_dword(in_block, in_block_offset)
                    operation = extract_bits(in_bytes, 0, 4)

                    if (operation & 0x0F) == 0x0F:
                        run_len = extract_bits(in_bytes, 4, 12)
                        out_byte = extract_bits(in_bytes, 16, 8)
                        in_bytes_consumed = 3
                        if run_len == 0:
                            run_len = extract_dword(in_block, in_block_offset + 3)
                            in_bytes_consumed += 4

                        for i in range(out_block_offset, out_block_offset + run_len + 1):
                            out_block[i] = out_byte
                        out_bytes_emitted = run_len

                    else:
                        segment_len = 3
                        if (operation & 0x0F) == 0x07:
                            segment_len += extract_bits(in_bytes, 4, 11)
                            out_relative_start_offset = extract_bits(in_bytes, 15, 17)
                            in_bytes_consumed = 4
                            if segment_len == 0 and out_relative_start_offset == 0:
                                segment_len = extract_dword(in_block, in_block_offset + 4)
                                out_relative_start_offset = extract_dword(in_block, in_block_offset + 8)
                                in_bytes_consumed += 8

                        elif (operation & 0x07) == 0x03:
                            segment_len += extract_bits(in_bytes, 3, 5)
                            out_relative_start_offset = extract_bits(in_bytes, 8, 16)
                            in_bytes_consumed = 3

                        elif (operation & 0x03) == 0x02:
                            segment_len += extract_bits(in_bytes, 2, 4)
                            out_relative_start_offset = extract_bits(in_bytes, 6, 10)
                            in_bytes_consumed = 2

                        elif (operation & 0x03) == 0x01:
                            out_relative_start_offset = extract_bits(in_bytes, 2, 14)
                            in_bytes_consumed = 2

                        elif (operation & 0x03) == 0x00:
                            out_relative_start_offset = extract_bits(in_bytes, 2, 6)
                            in_bytes_consumed = 1

                        out_block_start_offset = out_block_offset - out_relative_start_offset
                        for i in range(0, segment_len + 1):
                            out_byte = out_block[out_block_start_offset + i]
                            out_block[out_block_offset + i] = out_byte
                        out_bytes_emitted = segment_len

                in_block_offset += in_bytes_consumed
                out_block_offset += out_bytes_emitted
                control_flags >>= 1
            block_num += 1
            out_bytes += out_block

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
