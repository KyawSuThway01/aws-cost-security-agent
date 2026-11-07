"""Tiny fake AWS objects so tests never call the real AWS."""


class FakePaginator:
    def __init__(self, pages):
        self.pages = pages

    def paginate(self, **kwargs):
        return self.pages