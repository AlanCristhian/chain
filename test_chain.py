import unittest
from operator import add
from itertools import product

from chain import given, ANS


class GivenSuite(unittest.TestCase):
    def test_first_argument(self):
        message = R"Expected 'callable' or 'generator'. Got 'int'"
        with self.assertRaisesRegex(TypeError, message):
            given(9)(8).end

    def test_single_function(self):
        result = given(15)(lambda x: x + 15).end
        self.assertEqual(result, 30)

    def test_two_functions(self):
        result = given(15)(lambda x: x + 15)(str).end
        self.assertEqual(result, "30")

    def test_positional_arguments(self):
        result = given("a.c")(str.replace, ".", "b").end
        self.assertEqual(result, "abc")

    def test_explicit_positinonal_argument(self):
        result = given(9)(lambda x, y: 0/y, 0, ANS).end
        self.assertEqual(result, 0)

    def test_many_explicit_positinonal_argument(self):
        result = given(9)(lambda x, y, z: x*y*z, ANS, ANS, ANS).end
        self.assertEqual(result, 729)

    def test_keyword_arguments(self):
        result = given("a")(lambda x, y, z: x + y + z, y="b", z="c").end
        self.assertEqual(result, "abc")

    def test_explicit_keyword_arguments(self):
        result = given("z")(lambda x, y, z: x + y + z, x="x", y="y", z=ANS).end
        self.assertEqual(result, "xyz")

    def test_many_explicit_keyword_arguments(self):
        result = given("z")(lambda x, y, z: x + y + z, x=ANS, y=ANS, z=ANS).end
        self.assertEqual(result, "zzz")

    def test_positional_and_keyword_arguments(self):
        result = given(9)(lambda x, y: x + y, ANS, y=ANS).end
        self.assertEqual(result, 18)

    def test_single_generator(self):
        result = given([1, 2, 3])(i*2 for i in ANS)(list).end
        self.assertEqual(result, [2, 4, 6])

    def test_two_generators(self):
        result = given([1, 2, 3])(i*2 for i in ANS)(i*3 for i in ANS)(list).end
        self.assertEqual(result, [6, 12, 18])

    def test_many_for_statements(self):
        message = R"Multiple for statement are not supported."
        with self.assertRaisesRegex(SyntaxError, message):
            given([1, 2, 3])(i*j for i in range(3) for j in ANS).end

    def test_product_method(self):
        expected = [(i, j) for i in "abc" for j in range(4)]
        result = (given("abc")
                     (product, ANS, range(4))
                     ((i, j) for i, j in ANS)
                     (list)
                 .end)
        self.assertEqual(result, expected)

    def test_LAST_in_second_for_iter_statement(self):
        message = R"Can not iterate over 'list_iterator', " \
                  "'ANS' constant only."
        with self.assertRaisesRegex(ValueError, message):
            given("abc")(i for i in [1, 2]).end

    def test_generator_followed_with_a_second_argument(self):
        message = "Can not get arguments if you pass a generator "\
                  "at first \(3 given\)\."
        with self.assertRaisesRegex(TypeError, message):
            given("abc")((i for i in ANS), 1, 2, z=3).end


if __name__ == '__main__':
    unittest.main()
