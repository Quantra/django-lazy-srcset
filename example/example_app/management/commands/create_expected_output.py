from django.conf import settings
from django.core.management import BaseCommand

from lazy_srcset.tests.the_test import output_files_list, output_html


class Command(BaseCommand):
    help = (
        "Create the expected output files for the test. Only run this when you are certain you want to "
        "update the expected test output."
    )

    def handle(self, *args, **options):
        tests_dir = settings.BASE_DIR / "lazy_srcset" / "tests"

        expected_html_file = tests_dir / "expected_html.html"
        expected_html_file.write_text(output_html())

        expected_files_file = tests_dir / "expected_files.txt"
        expected_files_file.write_text(output_files_list())

        settings.LAZY_SRCSET_ENABLED = False
        expected_html_file_disabled = tests_dir / "expected_html_disabled.html"
        expected_html_file_disabled.write_text(output_html())

        expected_files_file_disabled = tests_dir / "expected_files_disabled.txt"
        expected_files_file_disabled.write_text("")
