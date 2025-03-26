import unittest

from nlb.util import introspection


class IntrospectionTest(unittest.TestCase):
    def test_parse_signature_and_docs(self):
        # Define a sample function with a docstring
        def sample_function(arg1: str, arg2: int) -> None:
            """This is a sample function.

            Args:
                arg1: The first argument.
                arg2: The second argument.

            Returns:
                None
            """
            pass

        # Parse the docstring
        parsed = introspection.parse_signature_and_docs(sample_function)

        # Check the parsed values
        self.assertEqual(parsed.description, "This is a sample function.")
        self.assertEqual(
            parsed.arg_descriptions,
            {'arg1': 'The first argument.', 'arg2': 'The second argument.'},
        )
        self.assertEqual(parsed.arg_types, {'arg1': str, 'arg2': int})
        self.assertEqual(parsed.return_description, 'None')
        self.assertIsNone(parsed.return_type)

        # Make a function with no return section
        def no_return_function(arg1: int) -> None:
            """This function has no return section.

            Args:
                arg1: The first argument.
            """
            pass

        # Parse the docstring
        parsed_no_return = introspection.parse_signature_and_docs(no_return_function)

        # Check the parsed values
        self.assertEqual(
            parsed_no_return.description, "This function has no return section."
        )
        self.assertEqual(
            parsed_no_return.arg_descriptions, {'arg1': 'The first argument.'}
        )
        self.assertEqual(parsed_no_return.arg_types, {'arg1': int})
        self.assertIsNone(parsed_no_return.return_description)
        self.assertIsNone(parsed_no_return.return_type)

        # Make a function with an optional arg
        def optional_arg_function(arg1: str, arg2: int | None) -> None:
            """This function has an optional argument.

            Args:
                arg1: The first argument.
                arg2: The second argument (optional).
            """
            pass

        # Parse the docstring
        parsed_optional_arg = introspection.parse_signature_and_docs(
            optional_arg_function
        )

        # Check the parsed values
        self.assertEqual(
            parsed_optional_arg.description, "This function has an optional argument."
        )
        self.assertEqual(
            parsed_optional_arg.arg_descriptions,
            {'arg1': 'The first argument.', 'arg2': 'The second argument (optional).'},
        )
        self.assertEqual(
            parsed_optional_arg.arg_types, {'arg1': str, 'arg2': int | None}
        )
        self.assertIsNone(parsed_optional_arg.return_description)
        self.assertIsNone(parsed_optional_arg.return_type)

        # Make a function with missing type hints
        def missing_type_hint_function(arg1, arg2):
            """This function has missing type hints.

            Args:
                arg1: The first argument.
                arg2: The second argument.
            """
            pass

        with self.assertRaises(ValueError):
            introspection.parse_signature_and_docs(missing_type_hint_function)

        # Make a function with a return section but no return type annotation
        def no_return_type_function(arg1: int):
            """This function has a return section but no return type annotation.

            Args:
                arg1: The first argument.

            Returns:
                A description of the return value.
            """
            pass

        with self.assertRaises(ValueError):
            introspection.parse_signature_and_docs(no_return_type_function)

        # Make a function with no args section
        def no_args_function():
            """This function has no args section."""
            pass

        with self.assertRaises(ValueError):
            introspection.parse_signature_and_docs(no_args_function)

        # Make a function with no docstring
        def no_docstring_function():
            pass

        with self.assertRaises(ValueError):
            introspection.parse_signature_and_docs(no_docstring_function)
