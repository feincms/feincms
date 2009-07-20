from feincms.module.page.extensions.navigation import NavigationExtension


class PassthroughExtension(NavigationExtension):
    # See PagesTestCase.test_23_navigation_extension
    name = 'passthrough extension'

    def children(self, page):
        for p in page.children.in_navigation():
            yield p
