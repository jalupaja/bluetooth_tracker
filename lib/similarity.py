from difflib import SequenceMatcher

DEBUG = False
class similarity:

    @staticmethod
    def calculate_similarity(value1, value2, checker_function = None):
        # a checker_function should take 2 values, compare them and return a floating point similarity value
        if checker_function is None:
            if isinstance(value1, str) and isinstance(value2, str):
                return similarity.text(value1, value2)
            elif isinstance(value1, (list, set, tuple)) and isinstance(value2, (list, set, tuple)):
                return similarity.list(value1, value2)
            elif isinstance(value1, (bytes, bytearray)) and isinstance(value2, (bytes, bytearray)):
                return similarity.binary(value1, value2)
            elif isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                return similarity.numeric(value1, value2)
            else:
                if DEBUG:
                    print(f"ERROR calculating similarity between {value1} and {value2}")
                return 0.0
        else:
            return checker_function(value1, value2)

    @staticmethod
    def exact(value1, value2):
        if (DEBUG):
            print(f"exact: {value1} : {value2} -> {value1 == value2}")
        return 1 if value1 == value2 else 0

    @staticmethod
    def text(text1, text2):
        if text1 is None or text2 is None \
                or text1 == "" \
                or text2 == "" \
                or text1 == "(bytearray(b'\\x00'),)" \
                or text2 == "(bytearray(b'\\x00'),)" \
                or text1 == "(None,)" \
                or text2 == "(None,)":
            return 0

        text1 = str(text1)
        text2 = str(text2)

        if DEBUG:
            print(f"text: '{text1}' : {text2} -> {SequenceMatcher(None, text1, text2).ratio()}")
        return SequenceMatcher(None, text1, text2).ratio()

    @staticmethod
    def list(list1, list2):
        if not list1 or not list2:
            return 0
        set1, set2 = set(list1), set(list2)

        set1.remove(None)
        set2.remove(None)

        if not set1 and not set2:
            return 0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        # TODO next step could be (if both are same length) to use calculate_similarity to mean over all items

        if DEBUG:
            print(f"list: {list1} : {list2} -> {intersection / union}")
        return intersection / union

    @staticmethod
    def hex(hex1, hex2):
        if not hex1 or not hex2:
            return 0

        bin1 = bin(int(hex1, 16))[2:]
        bin2 = bin(int(hex2, 16))[2:]
        return similarity.binary(bin1, bin2)

    @staticmethod
    def binary(binary1, binary2):
        # This will compare strings like "001001"
        if not binary1 or not binary2:
            return 0

        # match binary length
        total_bits = max(len(binary1), len(binary2))
        binary1 = binary1.rjust(total_bits, '0')
        binary2 = binary2.rjust(total_bits, '0')

        matching_bits = 0
        for b1, b2 in zip(binary1, binary2):
            if b1 == b2:
                matching_bits += 1

        if DEBUG:
            print(f"binary: {binary1} : {binary2} -> {matching_bits / total_bits}")
        return matching_bits / total_bits

    @staticmethod
    def numeric(num1, num2):
        # expect 0 to be None value
        if not num1 or not num2 or num1 == 0 or num2 == 0:
            return 0

        if num1 == num2:
            return 1.0

        try:
            num1 = int(num1)
            num2 = int(num2)
        except:
            return 0

        if DEBUG:
            print(f"num: {num1} : {num2} -> {1 - abs(num1 - num2) / max(abs(num1), abs(num2))}")
        return 1 - abs(num1 - num2) / max(abs(num1), abs(num2))

    @staticmethod
    def uuids(uuids1, uuids2):
        if not uuids1 or not uuids2:
            return 0

        uuids1 = uuids1.split(",")
        uuids2 = uuids2.split(",")

        matches = 0
        for uuid in uuids1:
            if uuid in uuids2:
                matches += 1

        max_matches = max(len(uuids1), len(uuids2))

        # weighted score
        return min(1, (matches * 2) / max_matches)

    @staticmethod
    def gatt_services(services1, services2):
        def calc_res(res, total_amount):
            if not res or total_amount == 0:
                return 0

            res = [r for r in res if r >= 0]
            good_matches = len([r for r in res if r > 0.8])
            partial_matches = sum(res)

            weight = 2
            weighted_score = (good_matches * weight) + partial_matches

            return min(weighted_score / total_amount, 1.0)

        def cmp_gatt(v1, v2):
            if v1.uuid == v2.uuid:
                if v1.description == v2.description:
                    if v1.value and v1.value == v2.value:
                        return 1
                    return 0.9
                return 0.5

        def cmp_char(char1, char2):
            val_res = cmp_gatt(char1, char2)
            res = []

            if val_res > 0.8:
                desc_map = {desc.handle: desc for desc in char2.descriptors}
                desc_res = []
                for desc1 in char1.descriptors:
                    desc2 = desc_map.get(desc1.handle)
                    if desc2:
                        desc_res.append(cmp_gatt(desc1, desc2))

                return calc_res(
                        desc_res,
                        max(len(char1.descriptors), len(char2.descriptors))
                        )
            else:
                return val_res

        res = []
        equal_svc = [s for s in services1 if s in services2]
        for handle in services1:
            if handle in services2:
                svc1 = services1[handle]
                svc2 = services2[handle]

                if svc1.uuid == svc2.uuid:
                    if svc1.description == svc2.description:
                        char_map = {char.handle: char for char in svc2.characteristics}
                        char_res = []
                        for char1 in svc1.characteristics:
                            char2 = char_map.get(char1.handle)
                            if char2:
                                char_res.append(cmp_char(char1, char2))

                        res.append(
                                calc_res(char_res, max(len(svc1.characteristics), len(svc2.characteristics)))
                                )

                    else:
                        res.append(0.4)

        sim_val = calc_res(res, max(len(services1), len(services2)))
        return sim_val

