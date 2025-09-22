import unittest
import os
from functions.get_file_content import get_file_content
from functions.get_files_info import get_files_info
from functions.write_file import write_file
from config import MAX_CHARS


class TestFileUtilities(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_folder"
        os.makedirs(self.test_dir, exist_ok=True)

        # Regular files
        with open(os.path.join(self.test_dir, "file1.txt"), "w") as f:
            f.write("Hello")
        with open(os.path.join(self.test_dir, "file2.txt"), "w") as f:
            f.write("World")

        # Subdirectory
        os.makedirs(os.path.join(self.test_dir, "subdir"), exist_ok=True)

        # Large file for truncation test
        with open(os.path.join(self.test_dir, "large_file.txt"), "w") as f:
            f.write("A" * (MAX_CHARS + 100))  # longer than MAX_CHARS

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    # Tests for get_files_info
    def test_list_files_default(self):
        result = get_files_info(self.test_dir)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)
        self.assertIn("subdir", result)

    def test_list_files_specific_directory(self):
        result = get_files_info(self.test_dir, "subdir")
        self.assertEqual(result, "")

    def test_invalid_directory(self):
        result = get_files_info(self.test_dir, "../")
        self.assertIn("error", result)

    # Tests for get_file_content
    def test_file_content_regular(self):
        result = get_file_content(self.test_dir, "file1.txt")
        self.assertEqual(result, "Hello")

    def test_file_content_invalid_file(self):
        result = get_file_content(self.test_dir, "nonexistent.txt")
        self.assertIn("error", result)

    def test_file_content_truncate(self):
        result = get_file_content(self.test_dir, "large_file.txt")
        self.assertIn(f"is truncated at {MAX_CHARS} characters", result)
        self.assertTrue(result.startswith("A" * 10))

    # Tests for write_file
    def test_write_file_regular(self):
        content = "New file content"
        result = write_file(self.test_dir, "new_file.txt", content)
        self.assertIn("Successfully wrote", result)

        # Check if content was actually written
        written_content = get_file_content(self.test_dir, "new_file.txt")
        self.assertEqual(written_content, content)

    def test_write_file_create_in_subdir(self):
        content = "Subdirectory file"
        result = write_file(self.test_dir, "subdir/file3.txt", content)
        self.assertIn("Successfully wrote", result)

        written_content = get_file_content(self.test_dir, "subdir/file3.txt")
        self.assertEqual(written_content, content)

    def test_write_file_outside_directory(self):
        content = "Invalid write"
        result = write_file(self.test_dir, "../outside.txt", content)
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
