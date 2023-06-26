from imagekit import ImageSpec, register
from pilkit.processors import ResizeToFit


class SrcsetImage(ImageSpec):
    """
    imagekit <3 custom generator for converting, compressing and proportionally resizing images to the given width.
    https://django-imagekit.readthedocs.io/en/latest/advanced_usage.html#specs-that-change
    """

    def __init__(self, width=None, output_format=None, quality=None, **kwargs):
        self.format = output_format
        self.processors = [ResizeToFit(width)]
        if quality is not None:
            self.options = {"quality": quality}
        super().__init__(**kwargs)


register.generator("lazy_srcset:srcset_image", SrcsetImage)
