from count_anywhere.libs.markers import (
    Group, ReferenceMarker
)

def test():
    marker = ReferenceMarker()
    i = getattr(ReferenceMarker.children, 'ignored', None)
    print(i)
    print(type(marker.children))

    group = Group(children=[])
    print(group.children)
