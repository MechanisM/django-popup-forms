"""Decorators for popup form processing views"""

from functools import wraps
from django.http import HttpResponseRedirect, Http404

class PopupFormValidationError(Exception):
    """Should be raised by view, processing PopUp form,
    instead of re-rendering this form in template.

    """

    def __init__(self, form):
        """Stores form instance in the exception"""
        self.form = form
        return super(PopupFormValidationError, self).__init__(
                u'Errors in form: {0}'.format(form.errors))


def popup_form(func):
    """Re-populate submitted popup form with error on referrer's page.

    Popup forms (for sending messages, inviting to events, etc.) are
    originally rendered hidden in the template, from which they should
    be sent. This decorator wraps a view processing submission
    of popup form.

    In case form processed by the view is not valid,
    the view should raise `PopupFormValidationError` exception,
    instead of re-populating form.

    This decorator puts the form with errors to session, and redirects
    back to original view, from where form was submitted. Then
    popup form is re-populated, showing all errors.

    .. IMPORTANT::
        * View should not render anything (i.e. return `HttpResponse`).
          It can only return `HttpResponseRedirect`).
        * If form validation failed, view should raise exception,
          passing form as only argument::

              if not form.is_valid():
                  raise PopupFormValidationError(form)

    """

    @wraps(func)
    def wrapper(request, *args, **kwargs):

        # Delete old popup form from session
        if 'popup_form' in request.session:
            del request.session['popup_form']

        # Try processing form. If form contains errors,
        # put it to session and redirect back to referrer.
        try:
            response = func(request, *args, **kwargs)
        except PopupFormValidationError, e:
            request.session['popup_form'] = request.path, e.form.data
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        if isinstance(response, HttpResponseRedirect):
            return response

        # The view should NOT populate form itself!
        if request.method == 'POST':
            raise ValueError('View for processing popup form populates it!')
        else:
            raise Http404

    return wrapper


