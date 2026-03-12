class LeadingZeroCounter:
    def count(self, digest: bytes) -> int:
        bit_count = 0
        for value in digest:
            if value == 0:
                bit_count += 8
                continue
            return bit_count + (8 - value.bit_length())
        return bit_count
