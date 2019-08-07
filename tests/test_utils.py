from tests.base import TestCase, main
from ocrd_utils import (
    abspath,

    bbox_from_points,
    bbox_from_xywh,

    concat_padded,
    is_local_filename,
    is_string,
    membername,

    points_from_bbox,
    points_from_x0y0x1y1,
    points_from_xywh,
    points_from_polygon,

    polygon_from_points,
    polygon_from_x0y0x1y1,

    xywh_from_points,
    xywh_from_polygon,
)
from ocrd_models.utils import xmllint_format

class TestUtils(TestCase):

    def test_abspath(self):
        self.assertEqual(abspath('file:///'), '/')

    def test_is_local_filename(self):
        self.assertEqual(is_local_filename('file:///'), True)

    def test_points_from_xywh(self):
        self.assertEqual(
            points_from_xywh({'x': 100, 'y': 100, 'w': 100, 'h': 100}),
            '100,100 200,100 200,200 100,200')

    def test_points_from_bbox(self):
        self.assertEqual(
            points_from_bbox(100, 100, 200, 200),
            '100,100 200,100 200,200 100,200')

    def test_points_from_polygon(self):
        self.assertEqual(
            points_from_polygon([[100, 100], [200, 100], [200, 200], [100, 200]]),
            '100,100 200,100 200,200 100,200')

    def test_polygon_from_x0y0x1y1(self):
        self.assertEqual(
            polygon_from_x0y0x1y1([100, 100, 200, 200]),
            [[100, 100], [200, 100], [200, 200], [100, 200]])

    def test_points_from_x0y0x1y1(self):
        self.assertEqual(
            points_from_x0y0x1y1([100, 100, 200, 200]),
            '100,100 200,100 200,200 100,200')

    def test_bbox_from_points(self):
        self.assertEqual(
            bbox_from_points('100,100 200,100 200,200 100,200'), (100, 100, 200, 200))

    def test_bbox_from_xywh(self):
        self.assertEqual(
            bbox_from_xywh({'x': 100, 'y': 100, 'w': 100, 'h': 100}),
            (100, 100, 200, 200))

    def test_xywh_from_polygon(self):
        self.assertEqual(
            xywh_from_polygon([[100, 100], [200, 100], [200, 200], [100, 200]]),
            {'x': 100, 'y': 100, 'w': 100, 'h': 100})

    def test_xywh_from_points(self):
        self.assertEqual(
            xywh_from_points('100,100 200,100 200,200 100,200'),
            {'x': 100, 'y': 100, 'w': 100, 'h': 100})

    def test_xywh_from_points_unordered(self):
        self.assertEqual(
            xywh_from_points('500,500 100,100 200,100 200,200 100,200'),
            {'x': 100, 'y': 100, 'w': 400, 'h': 400})

    def test_polygon_from_points(self):
        self.assertEqual(
            polygon_from_points('100,100 200,100 200,200 100,200'),
            [[100, 100], [200, 100], [200, 200], [100, 200]])

    def test_concat_padded(self):
        self.assertEqual(concat_padded('x', 0), 'x_0001')
        self.assertEqual(concat_padded('x', 0, 1, 2), 'x_0001_0002_0003')
        self.assertEqual(concat_padded('x', 0, '1', 2), 'x_0001_1_0003')

    def test_is_string(self):
        self.assertTrue(is_string('x'))
        self.assertTrue(is_string(u'x'))

    def test_xmllint(self):
        xml_str = '<beep>\n  <boop>42</boop>\n</beep>\n'
        pretty_xml = xmllint_format(xml_str).decode('utf-8')
        self.assertEqual(pretty_xml, '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str)

    def test_membername(self):
        class Klazz:
            def __init__(self):
                self.prop = 42
        instance = Klazz()
        self.assertEqual(membername(instance, 42), 'prop')


if __name__ == '__main__':
    main()
