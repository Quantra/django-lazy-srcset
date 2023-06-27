from pathlib import Path

from django.conf import settings
from django.core.files.images import ImageFile
from django.shortcuts import render


class TheImageFile(ImageFile):
    """
    An ImageFile with an url attribute. Should be close enough to what you get when using a models.ImageField
    """

    @property
    def url(self):
        name = Path(self.name).name
        return f"{settings.MEDIA_URL }{name}"


def the_view(request):
    images_dir = settings.MEDIA_ROOT
    images = [TheImageFile(open(i, "rb")) for i in images_dir.iterdir() if i.is_file()]

    print(images[0])
    print(dir(images[0]))

    return render(request, "the_template.html", {"images": images})
