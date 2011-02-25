"""
This is a collection of legacy code which is kept around for those who still
need it. No guarantees are given that the code still works at all (but we still
try.)
"""

class ContentProxy(object):
    """
    This proxy offers attribute-style access to the page contents of regions::

        >> page = Page.objects.all()[0]
        >> page.content.main
        [A list of all page contents which are assigned to the region with key 'main']
    """

    def __init__(self, item):
        self.item = item

    def __getattr__(self, attr):
        """
        Get all item content instances for the specified item and region

        If no item contents could be found for the current item and the region
        has the inherited flag set, this method will go up the ancestor chain
        until either some item contents have found or no ancestors are left.
        """
        if (attr.startswith('__')):
            raise AttributeError

        item = self.__dict__['item']

        return self.get_content(item, attr)

    def get_content(self, item, attr):
        template = item.template
        try:
            region = template.regions_dict[attr]
        except KeyError:
            return []

        def collect_items(obj):
            contents = obj._content_for_region(region)

            # go to parent if this model has a parent attribute
            # TODO: this should be abstracted into a property/method or something
            # The link which should be followed is not always '.parent'
            if region.inherited and not contents and hasattr(obj, 'parent_id') and obj.parent_id:
                return collect_items(obj.parent)

            return contents

        contents = collect_items(item)
        contents.sort(key=lambda c: c.ordering)
        return contents

