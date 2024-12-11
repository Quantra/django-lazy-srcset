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
            except (AttributeError, ValueError):  # pragma: no cover
                pass

        # These could include units E.g. px or pt so strip them out.
        width = re.sub(r"[^\d.]", "", width) if width is not None else None
        height = re.sub(r"[^\d.]", "", height) if height is not None else None

    return width, height


def sanitize_breakpoint(breakpoint):
    """
    Breakpoints must be integers.
    """
    try:
        return int(breakpoint)
    except ValueError:  # pragma: no cover
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

    size = size.replace(" ", "")
    try:
        size, units = int(size[:-2]), size[-2:]
    except (IndexError, ValueError):  # pragma: no cover
        raise TemplateSyntaxError(
            "Invalid size: %s\nBreakpoints must be integers.\nSizes must specify vw or px units or be integers."
            % size
        )

    if units not in ["px", "vw"]:
        raise TemplateSyntaxError(
            "Invalid size: %s\nUnits must be px or vw." % size
        )  # pragma: no cover

    return size, units


def get_config(kwargs):
    """
    Pop from kwargs as needed and set up the config dict ready for this run.
    After running this kwargs will only contain breakpoints if anything.
    """
    # Get the conf from the config kwarg or default and copy it so changes don't persist
    try:
        conf_key = kwargs.pop("config")
    except KeyError:
        conf_key = "default"
    conf = settings.LAZY_SRCSET[conf_key].copy()

    # Try to pop these from kwargs
    for key in ["default_size", "max_width", "quality", "threshold"]:
        try:
            conf[key] = kwargs.pop(key)
        except KeyError:
            pass

    # Set a default from settings
    conf.setdefault("threshold", settings.LAZY_SRCSET_THRESHOLD)
    conf.setdefault("generator_id", settings.LAZY_SRCSET_GENERATOR_ID)

    return conf


def svg_srcset(source_img):
    """
    Returns attrs string containing src and width and height if possible. Will also add role="img" attr.
    """
    # Try getting width and height from attrs.
    try:
        width = source_img.width
        height = source_img.height
    except AttributeError:  # pragma: no cover
        width, height = None, None

    # If we don't have the width and height try getting it from the SVG file.
    if width is None or height is None:
        width, height = get_svg_dimensions(source_img)

    # Return with width and height if we have them.
    if width is not None and height is not None:
        html = format_html(
            'src="{}" width="{}" height="{}" role="img"', source_img.url, width, height
        )
    else:
        # Return with src only if we don't have width and height
        html = format_html('src="{}" role="img"', source_img.url)

    source_img.close()
    return html


def noop(source_img):
    """
    The no-op returns src, width and height so images still work.
    This is used when LAZY_SRCSET_ENABLED=False and whilst images are being generated.
    """
    html = format_html(
        'src="{}" width="{}" height="{}"',
        source_img.url,
        source_img.width,
        source_img.height,
    )
    source_img.close()
    return html


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
    <!-- Any sizes set as args are ignored and config break points are ignored -->
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
    args = list(args)

    # If the image has an open method we should be good to go.  If not assume it's a string and get it from
    # staticfiles wrapped up in ImageFile. Set the url attribute, so we can use it later.
    source_img = args.pop(0)
    if not hasattr(source_img, "open"):
        url = staticfiles_storage.url(source_img)
        source_img = ImageFile(open(finders.find(source_img), "rb"))
        source_img.url = url

    file_extension = Path(source_img.name).suffix.lower()

    # Check if the file extension should be ignored
    if file_extension in [
        ext.lower() for ext in settings.LAZY_SRCSET_IGNORED_EXTENSIONS
    ]:
        return noop(source_img)

    # If the image is an SVG return now with src, width and height if possible. SVG is lazy king!
    if file_extension == ".svg":
        return svg_srcset(source_img)

    # If LAZY_SRCSET_ENABLED = False return src, width and height
    if not settings.LAZY_SRCSET_ENABLED:
        return noop(source_img)

    # Prepare config, sizes_dict and widths_dict
    conf = get_config(kwargs)

    # If we have kwargs we can set the sizes otherwise try and get them from args.
    sizes_dict = kwargs or lists_to_dict(conf["breakpoints"], args)

    # The sizes in our dict are strings and might contain px|vw. After this our dict will be like: {1920: (50, "vw")}
    sizes_dict = {
        sanitize_breakpoint(k): sanitize_size(v) for k, v in sizes_dict.items()
    }

    # Set the maximum width image in our srcset.
    if conf["max_width"] is None or conf["max_width"] > source_img.width:
        # Limit max_width to image.width or use image.width if max_width is None.
        conf["max_width"] = source_img.width

    # widths_dict is a dict with the image width as key and a boolean if the image must be created E.g. {960: True}
    widths_dict = {conf["max_width"]: True}

    # Loop through the sizes_dict to create the widths_dict used for image generation.  Create sizes list for the attr
    sizes = []
    width, units = "100", "vw"
    for breakpoint_width in sorted(sizes_dict.keys()):
        width, units = sizes_dict[breakpoint_width]

        # Add an entry to sizes
        sizes.append(
            format_html("(max-width: {}px) {}{}", breakpoint_width, width, units)
        )

        if units == "px":
            # When px units are defined always generate an image with that width
            widths_dict[width] = True
            continue

        # Calculate the target width for this breakpoint with some quick maths.
        target_width = math.ceil(breakpoint_width * width / 100)
        if target_width < conf["max_width"]:
            # Don't upscale images, that would require extra effort.
            widths_dict[target_width] = False

    # Add the default size (sneaky use of the sorted loop above leaves us with the width and units we need)
    if "default_size" in conf.keys():
        width, units = sanitize_size(conf["default_size"])
    sizes.append(format_html("{}{}", width, units))

    # Loop through the widths of images and generate what is needed
    current_width = conf["max_width"]
    output_imgs = []
    for width in reversed(sorted(widths_dict.keys())):
        if not widths_dict[width] and (current_width - width) < conf["threshold"]:
            # Only generate required images and images outside our threshold
            continue

        # Generate the image via imagekit.
        generator = generator_registry.get(
            conf["generator_id"],
            width=width,
            source=source_img,
            output_format=conf.get("format"),
            quality=conf["quality"],
        )
        generator_image = ImageCacheFile(generator)
        output_imgs.append(generator_image)

        current_width = width

    # Create the srcsets
    try:
        srcsets = [
            format_html("{} {}w", image.url, image.width) for image in output_imgs
        ]
    except FileNotFoundError:  # pragma: no cover
        # Images are being generated in another thread right now, but we can rely on source_img to actually exist
        return noop(source_img)

    source_img.close()

    # Stringify!
    return format_html(
        'src="{}" srcset="{}" sizes="{}" width="{}" height="{}"',
        output_imgs[0].url,
        ", ".join(srcsets),
        ", ".join(sizes),
        output_imgs[0].width,
        output_imgs[0].height,
    )
