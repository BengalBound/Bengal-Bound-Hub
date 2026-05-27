from django.template.context import BaseContext

def _basecontext_copy(self):
    """
    Monkey-patch for Python 3.14 compatibility with Django 4.2.
    In 3.14, `copy(super())` fails because it tries to copy the super proxy explicitly.
    """
    duplicate = object.__new__(type(self))
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate

BaseContext.__copy__ = _basecontext_copy
