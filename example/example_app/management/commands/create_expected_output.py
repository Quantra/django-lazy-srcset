from django.conf import settings
from django.core.management import BaseCommand

from example.example_app.views import output_files_list, the_html


class Command(BaseCommand):
    help = (
        "Create the expected output files for the test. Only run this when you are certain you want to "
        "update the expected test output."
    )

    def handle(self, *args, **options):
        tests_dir = settings.BASE_DIR / "example/example_app/tests"

        expected_html_file = tests_dir / "expected_html.html"
        expected_html_file.write_text(the_html())

        expected_files_file = tests_dir / "expected_files.txt"
        expected_files_file.write_text(output_files_list())