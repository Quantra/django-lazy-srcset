import math
import re
from pathlib import Path
from xml.etree import ElementTree

from django import template
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.images import ImageFile
from django.utils.safestring import mark_safe
from imagekit.cachefiles import ImageCacheFile
from imagekit.registry import generator_registry

from lazy_srcset.conf import settings

register = template.Library()


class FormatStrings:
    """
    Format strings for attrs and parts of attrs.
    """

    srcset_entry = "%s %iw"
    sizes_entry = "(max-width: %ipx) %ivw"
    size = "%ivw"

    # These get set in init.
    src = width = height = srcset = sizes = None

    def __init__(self):
        for attr in ["src", "width", "height", "srcset", "sizes"]:
            setattr(self, attr, f'{attr}="%s"')


format_strings = FormatStrings()


def lists_to_dict(keys, values, default_value=100):
    """
    Combine uneven lists into a dictionary padding values with default_value if the values list is shorter than the
    keys list.  If the values list is longer it will ignore any extra values.
    """
    combined_dict = {}
    for key, value in zip(keys, values):
        combined_dict[key] = value
    for key in keys[len(values):]:  # fmt: skip
        combined_dict[key] = default_value
    return combined_dict


def get_from_kwargs_or_conf(key, kwargs, conf):
    """
    Pop the key from kwargs and return if possible. If not get the key from conf and return even if its None.
    """
    try:
        return kwargs.pop(key)
    except KeyError:
        return conf.get(key)


def get_svg_dimensions(svg_file):
    """
    Try and get width and height from the svg file or return none for them if not possible.
    """
    with svg_file.open() as f:
        tree = ElementTree.parse(f)
        root = tree.getroot()

        # Get width and height from attributes if they are set.
        width, height = root.get("width"), root.get("height")

        # If width or height attributes are missing, get values from viewbox.
        if width is None or height is None:
            viewbox = root.get("viewBox")
            try:
                _, _, width, height = viewbox.split(" ")
            except (AttributeError, ValueError):
                pass

        # These could include units eg px or pt so strip them out.
        width = re.sub("\\D", "", width) if width is not None else None
        height = re.sub("\\D", "", height) if height is not None else None

    return width, height


def image_src(image):
    """
    Returns attrs string containing src and width and height if possible.
    Used when LAZY_SRCSET_ENABLED = False
    """
    attrs = [
        format_strings.src % image.url,
        format_strings.width % image.width,
        format_strings.height % image.height,
    ]

    return mark_safe(" ".join(attrs))


def svg_srcset(svg):
    """
    Returns attrs string containing src and width and height if possible. Will also add role="img" attr.
    """
    # SVG only needs a src attribute, role="img" help screen readers to correctly announce the SVG as an image.
    attrs = [format_strings.src % svg.url, 'role="img"']

    # Try getting width and height from attrs.
    try:
        width = svg.width
        height = svg.height
    except AttributeError:
        width, height = None, None

    # If we don't have the width and height try getting it from the SVG file.
    if width is None or height is None:
        width, height = get_svg_dimensions(svg)

    # Add width and height to our attrs if we have them.
    if width is not None and height is not None:
        attrs += [format_strings.width % width, format_strings.height % height]

    # todo replace with format_html https://docs.djangoproject.com/en/4.2/ref/utils/#django.utils.html.format_html
    # Stringification!
    return mark_safe(" ".join(attrs))


@register.simple_tag
def srcset(*args, **kwargs):
    """
    The srcset template tag will create srcset, sizes, src, width and height attributes for an <img> tag.

    The first arg must be an ImageField or subclass or a path to an image discoverable by static files.

    args can provide relative image sizes in vw for each breakpoint, if not provided 100vw is assumed.  These are
    integers which are used to calculate generated image sizes.  They must be in vw.  Sorry no calc() etc. allowed.
    Don't try too hard here! Close is good enough.

    kwargs can be used to provide breakpoints and the relative width for each breakpoint directly (ignoring the
    config breakpoints and args if you set them for some reason).

    The config with the key ``default`` is used unless you provide the config kwarg to specify another config to use.

    You can use the ``max_width`` and ``quality`` kwargs to override the config on a per-use basis.

    The default size (for any resolution above the biggest breakpoint) is set to the same as the biggest breakpoint
    by default. If you need to set the default size to something else use the ``default_size`` kwarg.

    Example usage (where image is a file-like e.g. ImageField or a string representing a path to a static file):

    <!-- All sizes assumed to be 100vw -->
    <img {% srcset image %} />

    <!-- First break point 25vw second break point 50vw all others 100vw -->
    <img {% srcset image 25 50 %} />

    <!-- Define breakpoints and sizes as kwargs (any sizes set as args are ignored + config is ignored) -->
    <img {% srcset image 1920=25 1024=50 %} />

    <!-- Use the config "custom_breakpoints" instead of "default" -->
    <img {% srcset image config="custom_breakpoints" %} />

    <!-- Specify max_width as a kwarg -->
    <img {% srcset image max_width=1920 %} />

    <!-- Specify image quality as a kwarg -->
    <img {% srcset image quality=50 %} />

    <!-- Specify default size as a kwarg (otherwise it is assumed to be the same as the biggest breakpoint) -->
    <img {% srcset image default_size=50 %} />
    """
    args = list(args)

    # If the image has an open method we should be good to go.  If not assume it's a string and get it from
    # staticfiles wrapped up in ImageFile. Set the url attribute, so we can use it later.
    image = args.pop(0)
    if not hasattr(image, "open"):
        url = staticfiles_storage.url(image)
        image = ImageFile(open(finders.find(image), "rb"))
        image.url = url

    # If the image is an SVG return now with src="whatever.svg" and width and height if possible. SVG is lazy king!
    if Path(image.name).suffix.lower() == ".svg":
        return svg_srcset(image)

    # If LAZY_SRCSET_ENABLED = False return src, width and height
    if not settings.LAZY_SRCSET_ENABLED:
        return image_src(image)

    # Get the conf from the config kwarg or default
    try:
        conf = settings.LAZY_SRCSET[kwargs.pop("config")]
    except KeyError:
        conf = settings.LAZY_SRCSET["default"]

    # Get the default size from kwargs
    try:
        default_size = kwargs.pop("default_size")
    except KeyError:
        default_size = None

    # Get the max_width from kwargs or conf.
    max_width = get_from_kwargs_or_conf("max_width", kwargs, conf)

    # Set the maximum width image in our srcset.
    if max_width is None or max_width > image.width:
        # Limit max_width to image.width or use image.width if max_width is None.
        max_width = image.width

    # Get the format and quality from kwargs or conf and wrap up together with source in generator_kwargs.
    # These will be used for every image generation.
    generator_kwargs = {
        "source": image,
        "output_format": conf.get("format"),
        "quality": get_from_kwargs_or_conf("quality", kwargs, conf),
    }

    # Make sure the image file is closed as soon as we can.
    image.close()

    # Big generator!  https://youtu.be/8W_VC_BgMjo
    generator_id = conf.get("generator_id", settings.LAZY_SRCSET_GENERATOR_ID)

    # Generate the max_width image via imagekit.
    generator = generator_registry.get(
        generator_id, width=max_width, **generator_kwargs
    )
    generator_image = ImageCacheFile(generator)

    # Set the max_width image as our src and include it in the srcset.
    src_value = generator_image.url
    srcset_values = [format_strings.srcset_entry % (generator_image.url, max_width)]

    # Set the width and height from the max_width image.
    width, height = generator_image.width, generator_image.height

    # If we have kwargs we can set the sizes otherwise try and get them from args.
    sizes_dict = (
        {int(k): int(v) for k, v in kwargs.items()}
        if kwargs
        else lists_to_dict(conf["breakpoints"], args)
    )
    # sizes_dict = kwargs or lists_to_dict(conf["breakpoints"], args)

    # The sizes in our dict are strings and might contain px|vw

    # Set the default size to match our relative width for the biggest breakpoint.
    # todo this might be in px so sanitize the output
    default_size = default_size or sizes_dict[max(sizes_dict.keys())]
    sizes = [format_strings.size % default_size]

    # Loop through the sizes_dict to create the sizes and srcset attrs and generate the scaled images.
    # todo need to do a 2 pass, first to collect sizes and second to generate images
    #   after the first pass the sizes should be reduced by removing any which are too similar in size
    for breakpoint_width, relative_width in sizes_dict.items():
        # Add an entry for this breakpoint to sizes.
        sizes.append(format_strings.sizes_entry % (breakpoint_width, relative_width))

        # todo this bit needs to change
        # Calculate the target width for this breakpoint with some quick maths.
        target_width = math.ceil(breakpoint_width * relative_width / 100)
        if target_width >= max_width:
            # Don't upscale images, that would require extra effort.
            continue

        # Generate the image via imagekit.
        generator = generator_registry.get(
            generator_id, width=target_width, **generator_kwargs
        )
        generator_image = ImageCacheFile(generator)

        # Add an entry for this image to the srcset.
        srcset_values.append(
            format_strings.srcset_entry % (generator_image.url, target_width)
        )

    # todo replace with format_html https://docs.djangoproject.com/en/4.2/ref/utils/#django.utils.html.format_html
    # Create the attrs list for imminent stringification.
    attrs = [
        format_strings.src % src_value,
        format_strings.srcset % ", ".join(srcset_values),
        format_strings.sizes % ", ".join(reversed(sizes)),
        format_strings.width % width,
        format_strings.height % height,
    ]

    # Stringify!
    return mark_safe(" ".join(attrs))
