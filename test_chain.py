import unittest
from itertools import product
from operator import add

from chain import given, ANS, WithTheObj


class GivenSuite(unittest.TestCase):
    def test_first_argument(self):
        description = R"Expected 'callable' or 'generator'. Got 'int'"
        with self.assertRaisesRegex(TypeError, description):
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
        result = given(9)(lambda x, y: x/y, 0, ANS).end
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
        description = R"Multiple for statement are not allowed."
        with self.assertRaisesRegex(SyntaxError, description):
            given([1, 2, 3])(i*j for i in range(3) for j in ANS).end

    def test_product_method(self):
        expected = [(i, j) for i in "abc" for j in range(4)]
        result = (given("abc")
                     (product, ANS, range(4))
                     ((i, j) for i, j in ANS)
                     (list)
                 .end)
        self.assertEqual(result, expected)

    def test_ANS_in_second_for_iter_statement(self):
        description = R"Can not iterate over 'tuple_iterator', "\
                      "'ANS' constant only."
        with self.assertRaisesRegex(ValueError, description):
            given("abc")(i for i in (1, 2)).end

    def test_generator_followed_with_a_second_argument(self):
        description = "Can not accept arguments if you pass "\
                      "a generator at first \(3 given\)\."
        with self.assertRaisesRegex(TypeError, description):
            given("abc")((i for i in ANS), 1, 2, z=3).end


class ToTheGivenObjSuite(unittest.TestCase):
    def test_functions(self):
        operation = WithTheObj(add, 2)(add, 3)(add, 4)(add, 5)(add, 6).end
        self.assertEqual(operation(1), 21)

    def test_function_name(self):
        operation = WithTheObj(add, 2).end
        self.assertEqual(operation.__name__, "operation")
        self.assertEqual(operation.__qualname__, "chain.Function")

    def test_generator_copy(self):
        operation = (WithTheObj
                        (n for n in ANS if n%2 == 0)
                        (n + 2 for n in ANS)
                        (list)
                    .end)
        self.assertEqual(operation([1, 2, 3, 4, 5, 6]), [4, 6, 8])
        self.assertEqual(operation([7, 8, 9, 10, 11, 12]), [10, 12, 14])


if __name__ == '__main__':
    unittest.main()
