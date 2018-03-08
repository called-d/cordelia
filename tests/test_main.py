import unittest

dictionary_file = "dict.json"

class TestDictionaryTestCase(unittest.TestCase):
    def test_dictionary_load(self):
        import json
        with open(dictionary_file) as f:
            self.dic = json.load(f)
        return self.dic

if __name__ == "__main__":
    unittest.main()