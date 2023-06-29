from django.http import HttpResponse

from lazy_srcset.tests.the_test import output_html


def the_view(request):
    """
    We can use this view to check the output of the_test in the browser and confirm things are working as expected.
    """
    return HttpResponse(output_html())
