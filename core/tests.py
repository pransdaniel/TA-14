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

    def test_extract_short_answer(self):
        types = extract_question_types("Buat soal isian singkat")
        self.assertIn('short_answer', types)
        types2 = extract_question_types("soal short answer")
        self.assertIn('short_answer', types2)

    def test_validate_question_types_filters(self):
        data = [
            {'type': 'multiple_choice'},
            {'type': 'true_false'},
            {'type': 'short_answer'},
            {'type': 'essay'},
            {'type': 'unknown'},
        ]
        filtered = validate_question_types(data, ['true_false', 'short_answer', 'essay'])
        self.assertEqual(filtered, [data[1], data[2], data[3]])

    def test_prompt_formatting_with_short_answer(self):
        # ensure f-string escaping doesn't raise when short_answer included
        from .utils import question_gen
        class DummyModel:
            def generate_content(self, prompt):
                class R:
                    text = '[]'
                return R()
        orig = question_gen.model
        question_gen.model = DummyModel()
        try:
            question_gen.generate_questions_gemini("abc", "Buat soal short answer", num_questions=1)
        finally:
            question_gen.model = orig
