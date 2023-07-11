import math
import re
from pathlib import Path
from xml.etree import ElementTree

from django import template
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.images import ImageFile
from django.template.exceptions import TemplateSyntaxError
from django.utils.html import format_html
from imagekit.cachefiles import ImageCacheFile
from imagekit.registry import generator_registry

from lazy_srcset.conf import settings

register = template.Library()


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

        # These could include units E.g. px or pt so strip them out.
        width = re.sub("\\D", "", width) if width is not None else None
        height = re.sub("\\D", "", height) if height is not None else None

    return width, height


def sanitize_breakpoint(breakpoint):
    """
    Breakpoints must be integers.
    """
    try:
        return int(breakpoint)
    except ValueError:
        raise TemplateSyntaxError(
            "Invalid breakpoint: %s\nBreakpoints must be integers." % breakpoint
        )


def sanitize_size(size):
    """
    Sizes need to be either an integer or a string with px or vw units.
    """
    try:
        return int(size), "vw"
    except ValueError:
        pass

    try:
        size, units = int(size[:-2]), size[-2:]
    except (IndexError, ValueError):
        raise TemplateSyntaxError(
            "Invalid size: %s\nBreakpoints must be integers.\nSizes must specify vw or px units or be integers."
            % size
        )

    if units not in ["px", "vw"]:
        raise TemplateSyntaxError("Invalid size: %s\nUnits must be px or vw." % size)

    return size, units


def svg_srcset(svg):
    """
    Returns attrs string containing src and width and height if possible. Will also add role="img" attr.
    """
    # Try getting width and height from attrs.
    try:
        width = svg.width
        height = svg.height
    except AttributeError:
        width, height = None, None

    # If we don't have the width and height try getting it from the SVG file.
    if width is None or height is None:
        width, height = get_svg_dimensions(svg)

    # Return with width and height if we have them.
    if width is not None and height is not None:
        return format_html(
            'src="{}" width="{}" height="{}" role="img"', svg.url, width, height
        )

    # Return with src only if we don't have width and height
    return format_html('src="{}" role="img"', svg.url)


@register.simple_tag
def srcset(*args, **kwargs):
    """
    The srcset template tag will create srcset, sizes, src, width and height attributes for an <img> tag.

    The first arg must be an ImageField or subclass or a path to an image discoverable by static files.

    args can provide relative image sizes in vw for each break point, if not provided 100vw is assumed.  These are
    integers which are used to calculate generated image sizes.  They must have units of vw or px only. If no units
    are supplied then vw is assumed.

    kwargs can be used to provide break points and the relative size for each break point directly (ignoring the
    config break points and args if you set them for some reason).

    The config with the key ``default`` is used unless you provide the config kwarg to specify another config to use.

    You can use the ``max_width``, ``threshold`` and ``quality`` kwargs to override the config on a per-use basis.

    The default size (for any resolution above the biggest break point) is set to the same as the biggest break point
    by default. If you want to set the default size to something else use the ``default_size`` kwarg.

    Example usage (where image is a file-like e.g. ImageField or a string representing a path to a static file):

    <!-- All sizes assumed to be 100vw -->
    <img {% srcset image %} />

    <!-- First break point 25vw second break point 50vw all others 100vw -->
    <img {% srcset image 25 50 %} />

    <!-- These are all the valid ways to specify sizes as args -->
    <img {% srcset image 25 '50vw' '300px' %}

    <!-- Define break points and sizes as kwargs -->
    <!-- Any sizes set as args are ignored + config break points are ignored -->
    <img {% srcset image 1920=25 1024=50 %} />

    <!-- These are all the valid ways to specify break points and sizes as kwargs -->
    <img {% srcset image 1920=25 1024='50vw' 640='300px' %} />

    <!-- Use the config "custom_breakpoints" instead of "default" -->
    <img {% srcset image config='custom_breakpoints' %} />

    <!-- Specify max_width as a kwarg -->
    <img {% srcset image max_width=1920 %} />

    <!-- Specify image quality as a kwarg -->
    <img {% srcset image quality=50 %} />

    <!-- Specify threshold as a kwarg -->
    <img {% srcset image threshold=100 %} />

    <!-- Specify default size as a kwarg (otherwise it is assumed to be the same as the biggest breakpoint) -->
    <img {% srcset image default_size=50 %} />

    <!-- You can set the default size with units in the same way as the sizes args -->
    <img {% srcset image default_size='300px' %} />

    <!-- You can mix and match all of the above E.g. -->
    <img {% srcset image 25 33 50 config='custom_breakpoints' max_width=1920 image_quality=50 threshold=100 %} />
    <img {% srcset image 1920=25 1024=50 default_size=50 image_quality=50 %} />
    """
    # INIT
    args = list(args)

    # If the image has an open method we should be good to go.  If not assume it's a string and get it from
    # staticfiles wrapped up in ImageFile. Set the url attribute, so we can use it later.
    image = args.pop(0)
    if not hasattr(image, "open"):
        url = staticfiles_storage.url(image)
        image = ImageFile(open(finders.find(image), "rb"))
        image.url = url

    # If the image is an SVG return now with src, width and height if possible. SVG is lazy king!
    if Path(image.name).suffix.lower() == ".svg":
        return svg_srcset(image)

    # If LAZY_SRCSET_ENABLED = False return src, width and height
    if not settings.LAZY_SRCSET_ENABLED:
        return format_html(
            'src="{}" width="{}" height="{}"', image.url, image.width, image.height
        )

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

    # Get the kwargs for the image generator
    output_format = conf.get("format")
    quality = get_from_kwargs_or_conf("quality", kwargs, conf)
    generator_id = conf.get("generator_id", settings.LAZY_SRCSET_GENERATOR_ID)
    threshold = int(
        get_from_kwargs_or_conf("threshold", kwargs, conf)
        or settings.LAZY_SRCSET_THRESHOLD
    )

    # All kwargs except breakpoint kwargs must be popped by now!

    # If we have kwargs we can set the sizes otherwise try and get them from args.
    sizes_dict = kwargs or lists_to_dict(conf["breakpoints"], args)

    # The sizes in our dict are strings and might contain px|vw
    # After this our dict will be like: {1920: (50, "vw")}
    sizes_dict = {
        sanitize_breakpoint(k): sanitize_size(v) for k, v in sizes_dict.items()
    }

    # Create the sizes for the sizes attr
    sizes = [
        format_html("(max-width: {}px) {}{}", size, *sizes_dict[size])
        for size in sorted(sizes_dict.keys())
    ]

    # Add the default size
    if default_size is not None:
        default_size = sanitize_size(default_size)
    else:
        default_size = sizes_dict[max(sizes_dict.keys())]
    sizes.append(format_html("{}{}", *default_size))

    # Set the maximum width image in our srcset.
    if max_width is None or max_width > image.width:
        # Limit max_width to image.width or use image.width if max_width is None.
        max_width = image.width

    # widths_dict will be a dict with the image width as key and a boolean if the image must be created E.g.
    # {960: True}
    widths_dict = {max_width: True}

    # Make sure the image file is closed as soon as we can.
    image.close()

    # GO!

    # Loop through the sizes_dict to create the widths_dict used for image generation.
    for breakpoint_width, (width, units) in sizes_dict.items():
        if units == "px":
            # When px units are defined always generate an image with that width
            widths_dict[width] = True
            continue

        # Calculate the target width for this breakpoint with some quick maths.
        target_width = math.ceil(breakpoint_width * width / 100)
        if target_width < max_width:
            # Don't upscale images, that would require extra effort.
            widths_dict[target_width] = False

    # Loop through the widths of images and generate what is needed
    current_width = max_width
    images = []
    for width in reversed(sorted(widths_dict.keys())):
        if not widths_dict[width] and (current_width - width) < threshold:
            # Only generate required images and images outside our threshold
            continue

        current_width = width

        # Generate the image via imagekit.
        generator = generator_registry.get(
            generator_id,
            width=width,
            source=image,
            output_format=output_format,
            quality=quality,
        )
        generator_image = ImageCacheFile(generator)
        images.append(generator_image)

    # Create the srcsets
    srcsets = [format_html("{} {}w", image.url, image.width) for image in images]

    # Stringify!
    return format_html(
        'src="{}" srcset="{}" sizes="{}" width="{}" height="{}"',
        images[0].url,
        ", ".join(srcsets),
        ", ".join(sizes),
        images[0].width,
        images[0].height,
    )
