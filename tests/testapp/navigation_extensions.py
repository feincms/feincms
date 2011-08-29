from feincms.module.page.extensions.navigation import NavigationExtension, PagePretender


class PassthroughExtension(NavigationExtension):
    # See PagesTestCase.test_23_navigation_extension
    name = 'passthrough extension'

    def children(self, page):
        for p in page.children.in_navigation():
            yield p


class PretenderExtension(NavigationExtension):
    name = 'pretender extension'

    def children(self, page):
        return [PagePretender(title='blabla', url='/asdsa/')]
