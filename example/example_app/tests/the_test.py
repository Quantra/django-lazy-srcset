import os

from django.conf import settings

from example.example_app.views import output_files_list, the_html


def test():
    example_dir = settings.BASE_DIR / "example"
    output_dir = example_dir / "images/output"

    tests_dir = example_dir / "example_app/tests"
    expected_html_file = tests_dir / "expected_html.html"
    expected_files_file = tests_dir / "expected_files.txt"

    expected_html = expected_html_file.read_text()
    expected_files = expected_files_file.read_text()

    # Empty the output dir
    for f in output_dir.glob("*"):
        if f.is_file():
            f.unlink()

    # Assert the output dir is empty
    assert not any(output_dir.iterdir())

    # Assert the_html matches the expected html - this will also generate images
    assert the_html() == expected_html

    # Assert the files created matches the expected files
    assert output_files_list() == expected_files

    # Get the creation timestamp of like one file
    like_one_file = ""
    create_date = None
    for f in output_dir.iterdir():
        if f.is_file():
            like_one_file = str(f)
            create_date = os.path.getmtime(like_one_file)
            break

    # Go again
    the_html()

    # Assert the file wasn't recreated
    assert os.path.getmtime(like_one_file) == create_date

    # Assert the list of files hasn't changed
    assert output_files_list() == expected_files