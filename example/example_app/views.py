import itertools
from pathlib import Path

from django.conf import settings
from django.core.files.images import ImageFile
from django.http import HttpResponse
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
        [None, ["relative-widths-50-33", "50 33"]],
        [None, ["breakpoints-widths-1234=56-789=10", "1234=56 789=10"]],
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
    output_dir = settings.BASE_DIR / "example/images/output"
    files = [
        f.name
        for f in sorted(output_dir.iterdir())
        if f.is_file() and not f.name.startswith(".")
    ]
    return "\n".join(files)


def the_view(request):
    return HttpResponse(output_html())
