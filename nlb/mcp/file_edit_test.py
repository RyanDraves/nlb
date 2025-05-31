import pathlib
import tempfile
import unittest

from fastmcp import exceptions

from nlb.mcp import file_edit


class FileEditToolTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tmp_dir_path = pathlib.Path(self._tmp_dir.name)
        self._edit_tool = file_edit.FileEditTool(sandbox_dir=self._tmp_dir_path)

    def test_file_view(self) -> None:
        # File doesn't exist
        with self.assertRaises(exceptions.ToolError):
            self._edit_tool.file_view('test.txt', 1, -1)

        # Create a file
        file_path = self._tmp_dir_path / 'test.txt'
        file_path.write_text(
            'Goodbye World\nGoodbye World\nGoodbye World\nGoodbye World\n'
        )

        # View the entire file
        resp = self._edit_tool.file_view('test.txt', 1, -1)
        self.assertEqual(
            '1: Goodbye World\n2: Goodbye World\n3: Goodbye World\n4: Goodbye World\n',
            resp,
        )

        # Other way to view the entire file
        resp = self._edit_tool.file_view('test.txt', None, None)
        self.assertEqual(
            '1: Goodbye World\n2: Goodbye World\n3: Goodbye World\n4: Goodbye World\n',
            resp,
        )

        # View a specific range of lines
        resp = self._edit_tool.file_view('test.txt', 2, 3)
        self.assertEqual('2: Goodbye World\n3: Goodbye World\n', resp)

        # View to the end of the file
        resp = self._edit_tool.file_view('test.txt', 2, -1)
        self.assertEqual('2: Goodbye World\n3: Goodbye World\n4: Goodbye World\n', resp)

        # View a single line
        resp = self._edit_tool.file_view('test.txt', 2, 2)
        self.assertEqual('2: Goodbye World\n', resp)

        # View with invalid start line
        with self.assertRaises(exceptions.ToolError):
            self._edit_tool.file_view('test.txt', 0, -1)

        # View with invalid end line
        with self.assertRaises(exceptions.ToolError):
            self._edit_tool.file_view('test.txt', 2, 1)

    def test_directory_view(self) -> None:
        # Directory doesn't exist
        with self.assertRaises(exceptions.ToolError):
            self._edit_tool.file_view('non_existent_dir', None, None)

        # Create a directory
        dir_path = self._tmp_dir_path / 'test_dir'
        dir_path.mkdir()

        # View empty directory
        resp = self._edit_tool.file_view('test_dir', None, None)
        self.assertEqual('test_dir directory contents: ', resp)

        # Create a file & directory in the directory
        (dir_path / 'file1.txt').touch()
        (dir_path / 'file2.txt').touch()
        (dir_path / 'sub_dir').mkdir()
        resp = self._edit_tool.file_view('test_dir', None, None)
        # Order is arbitrary; test for presence of all items
        self.assertIn('test_dir directory contents: ', resp)
        self.assertIn('file1.txt', resp)
        self.assertIn('file2.txt', resp)
        self.assertIn('sub_dir/', resp)

        # Place a file in the subdirectory, observe only the top-level directory is shown
        (dir_path / 'sub_dir' / 'file3.txt').touch()
        # Order is arbitrary; test for presence of all items
        self.assertIn('test_dir directory contents: ', resp)
        self.assertIn('file1.txt', resp)
        self.assertIn('file2.txt', resp)
        self.assertIn('sub_dir/', resp)

        # View the sandbox directory itself
        resp = self._edit_tool.file_view('', None, None)
        self.assertEqual('. directory contents: test_dir/', resp)

    def test_file_create(self) -> None:
        # Create a file in the sandbox directory
        resp = self._edit_tool.file_create('test.txt', 'Hello World')
        self.assertEqual('File test.txt created successfully.', resp)

        # Check the file contents
        file_path = self._tmp_dir_path / 'test.txt'
        self.assertTrue(file_path.exists())
        self.assertEqual('Hello World', file_path.read_text())

        # Attempt to create the same file again
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_create('test.txt', 'Goodbye World')
            self.assertEqual('Path test.txt already exists.', str(context.exception))

        # Check that the file contents have not changed
        self.assertEqual('Hello World', file_path.read_text())

    def test_file_update(self) -> None:
        # Create a file in the sandbox directory
        file_path = self._tmp_dir_path / 'test.txt'
        file_path.write_text('Hello World')

        # Update the file with new content
        self._edit_tool.file_update('test.txt', 'Goodbye World')

        # Check the file contents
        self.assertEqual('Goodbye World', file_path.read_text())

        # Attempt to update a non-existent file
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_update('non_existent.txt', 'Hello Again')
            self.assertEqual(
                'Path non_existent.txt does not exist.', str(context.exception)
            )
        # Check that the path does not exist
        self.assertFalse((self._tmp_dir_path / 'non_existent.txt').exists())

        # Make a directory and attempt to update it
        dir_path = self._tmp_dir_path / 'test_dir'
        dir_path.mkdir()
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_update('test_dir', 'Hello Again')
            self.assertEqual('Path test_dir is not a file.', str(context.exception))

    def test_undo_edit(self) -> None:
        # Create a file in the sandbox directory
        file_path = self._tmp_dir_path / 'test.txt'
        file_path.write_text('Hello World')

        # Attempt to undo an edit on the freshly created file
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_undo_edit('test.txt')
            self.assertEqual('No edits to undo for test.txt.', str(context.exception))

        # Update the file with new content
        self._edit_tool.file_update('test.txt', 'Goodbye World')

        # Undo the last edit
        self._edit_tool.file_undo_edit('test.txt')

        # Check the file contents
        self.assertEqual('Hello World', file_path.read_text())

        # Attempt to undo an edit on a non-existent file
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_undo_edit('non_existent.txt')
            self.assertEqual(
                'Path non_existent.txt does not exist.', str(context.exception)
            )
        # Check that the path does not exist
        self.assertFalse((self._tmp_dir_path / 'non_existent.txt').exists())

        # Make a directory and attempt to undo an edit on it
        dir_path = self._tmp_dir_path / 'test_dir'
        dir_path.mkdir()
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_undo_edit('test_dir')
            self.assertEqual('Path test_dir is not a file.', str(context.exception))

    def test_semantic_errors(self) -> None:
        # Create a file
        file_path = self._tmp_dir_path / 'test2.txt'
        file_path.touch()

        # Attempt to view a similar file with a different name
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_view('test.txt', 1, -1)
            self.assertEqual(
                'Path test.txt does not exist. Did you mean "test2.txt"?',
                str(context.exception),
            )

    def test_sandbox_breakout(self) -> None:
        # Attempt to create a file outside the sandbox directory
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_create('../outside.txt', 'Hello World')
            self.assertEqual(
                'Path ../outside.txt is not within the sandbox directory.',
                str(context.exception),
            )

        # Attempt to update a file outside the sandbox directory
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_update('../outside.txt', 'Goodbye World')
            self.assertEqual(
                'Path ../outside.txt is not within the sandbox directory.',
                str(context.exception),
            )

        # Attempt to view a file outside the sandbox directory
        with self.assertRaises(exceptions.ToolError) as context:
            self._edit_tool.file_view('../outside.txt', 1, -1)
            self.assertEqual(
                'Path ../outside.txt is not within the sandbox directory.',
                str(context.exception),
            )
