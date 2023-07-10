import itertools
import os
from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.images import ImageFile
from django.template import Context, Template


class DummyImageField(ImageFile):
    """
    An ImageFile with an url attribute. Should be close enough to what you get when using a models.ImageField
    """

    @property
    def filename(self):
        return Path(self.name).name

    @property
    def url(self):
        return f"{settings.MEDIA_URL }{self.filename}"


def output_html():
    """
    This will create a template to render using all combinations of the params supplied.
    Then it will render that template with all images in the example/images directory.
    We can then compare the output and contents of the images/output directory to some expected output in our test.
    We can also visit / in our browser to view the result.

    It's going to create a lot of images if they don't exist yet so be a little patient.
    """
    images_dir = settings.MEDIA_ROOT
    image_suffixes = [".webp", ".png", ".jpg", ".jpeg", ".svg"]
    images = [
        DummyImageField(open(i, "rb"))
        for i in sorted(images_dir.iterdir())
        if i.is_file() and i.suffix.lower() in image_suffixes
    ]

    template = "{%% load lazy_srcset %%}{%% for image in images %%}%s{%% endfor %%}"
    template_tag = '<img {%% srcset %s %%} alt="%s" />'

    template_tag_params = [
        [["image-file", "image"], ["image-static", "image.filename"]],
        [None, ["relative-widths-33-50", "33 50"]],
        [None, ["breakpoints-widths-1234=56-789=90", "1234=56 789=90"]],
        [None, ["custom-config-custom", 'config="custom"']],
        [None, ["quality-50", "quality=50"]],
        [None, ["max-width-800", "max_width=800"]],
    ]
    template_tag_params = itertools.product(*template_tag_params)

    template_tags = []
    for combo in template_tag_params:
        params = " ".join([p[1] for p in combo if p is not None])
        alt = " ".join([p[0] for p in combo if p is not None])
        template_tags.append(template_tag % (params, alt))

    template = template % "\n".join(template_tags)

    template = Template(template)
    context = Context({"images": images})
    return template.render(context)


def output_files_list():
    output_dir = settings.MEDIA_ROOT / settings.IMAGEKIT_CACHEFILE_DIR
    files = [
        f.name
        for f in sorted(output_dir.iterdir())
        if f.is_file() and not f.name.startswith(".")
    ]
    return "\n".join(files)


@pytest.mark.parametrize(
    "enabled,html_file,files_file",
    [
        [True, "expected_html.html", "expected_files.txt"],
        [False, "expected_html_disabled.html", "expected_files_disabled.txt"],
    ],
)
def test_lazy_srcset(settings, enabled, html_file, files_file):
    """
    One test that will run through all combinations of params and check the template tag output matches the
    expected output in the expected_html.html file.  It will also generate all the images and check they also match
    the expected out.  The test will expect the test images to be present in the MEDIA_ROOT directory as per the
    example project.
    """
    settings.LAZY_SRCSET_ENABLED = enabled

    output_dir = settings.MEDIA_ROOT / settings.IMAGEKIT_CACHEFILE_DIR

    tests_dir = Path(__file__).parent
    expected_html_file = tests_dir / html_file
    expected_files_file = tests_dir / files_file

    expected_html = expected_html_file.read_text()
    expected_files = expected_files_file.read_text()

    # Empty the output dir
    for f in output_dir.glob("*"):
        if f.is_file():
            f.unlink()

    # Assert the output dir is empty
    assert not any(output_dir.iterdir())

    # Assert output_html matches the expected html - this will also generate images
    assert output_html() == expected_html

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

    if enabled:
        # Go again
        output_html()

        # Assert the file wasn't recreated
        assert os.path.getmtime(like_one_file) == create_date

        # Assert the list of files hasn't changed
        assert output_files_list() == expected_files
