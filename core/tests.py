from django.test import TestCase
from .utils.question_gen import extract_question_types, validate_question_types


class QuestionGenUtilsTests(TestCase):
    def test_extract_question_types_defaults(self):
        # jika instruksi kosong -> return multiple_choice
        self.assertEqual(extract_question_types(""), ['multiple_choice'])
        self.assertEqual(extract_question_types("boleh buat pilihan ganda"), ['multiple_choice'])

    def test_extract_true_false(self):
        # kata kunci benar salah
        types = extract_question_types("Buat soal true/false tentang sejarah")
        self.assertIn('true_false', types)
        # support variabel lain
        types2 = extract_question_types("soal benar salah atau tf")
        self.assertIn('true_false', types2)

    def test_validate_question_types_filters(self):
        data = [
            {'type': 'multiple_choice'},
            {'type': 'true_false'},
            {'type': 'essay'},
            {'type': 'unknown'},
        ]
        filtered = validate_question_types(data, ['true_false', 'essay'])
        self.assertEqual(filtered, [data[1], data[2]])
