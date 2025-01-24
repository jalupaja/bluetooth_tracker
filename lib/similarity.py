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
    def binary(binary1, binary2):
        if binary1 and binary2:
            return 0

        # match binary length
        max_length = max(len(binary1), len(binary2))
        binary1 = binary1.ljust(max_length, b'\x00')
        binary2 = binary2.ljust(max_length, b'\x00')

        matching_bits = sum(bin(byte1 ^ byte2).count('0') - 1 for byte1, byte2 in zip(binary1, binary2))
        total_bits = max_length * 8

        if DEBUG:
            print(f"binary: {binary1} : {binary2} -> {matching_bits / total_bits}")
        return matching_bits / total_bits

    @staticmethod
    def numeric(num1, num2):
        # expect 0 to be None value
        if num1 is None or num2 is None or num1 == 0 or num2 == 0:
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

