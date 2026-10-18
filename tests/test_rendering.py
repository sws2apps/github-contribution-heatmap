import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from lxml import etree
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from widget import render_map_only, render_map_with_list, load_map_svg, get_color, get_color_dark
from main import app

class RenderingTests(unittest.TestCase):
    def test_all_country_colors_and_unique_ids(self):
        paths = load_map_svg().findall('{http://www.w3.org/2000/svg}path')
        self.assertEqual(len(paths), 256)
        counts = {p.get('id').lower().split('-')[0]: i + 1 for i, p in enumerate(paths)}
        for renderer in (render_map_only, render_map_with_list):
            for theme in ('light', 'dark'):
                with self.subTest(renderer=renderer.__name__, theme=theme):
                    root = etree.fromstring(renderer(counts, theme))
                    fills = root.xpath('//*[@class="country-fill"]')
                    self.assertEqual(len(fills), 256)
                    color = get_color_dark if theme == 'dark' else get_color
                    for p in fills:
                        self.assertEqual(p.get('fill'), color(counts[p.get('id').lower().split('-')[0]], max(counts.values())))
                    ids = root.xpath('//@id')
                    self.assertEqual(len(ids), len(set(ids)))
                    self.assertEqual(root.get('data-map-version'), 'mercator-v2')
                    credits = root.xpath('//*[local-name()="text" and contains(text(), "amcharts.com")]')
                    self.assertEqual(len(credits), 1)
                    self.assertEqual(len(root.xpath('//*[local-name()="metadata"]')), 1)
    def test_empty(self):
        for renderer in (render_map_only, render_map_with_list):
            for theme in ('light', 'dark'):
                root = etree.fromstring(renderer({}, theme))
                self.assertIn('0 COUNTRIES', ''.join(root.itertext()))
    def test_route_location_mapping_and_refresh(self):
        users = [{'location': v} for v in ('Germany', 'Berlin', 'Nigeria', 'Niger', 'Russia')]
        with patch('widget.get_all_contributors', return_value=users) as fetch:
            response = app.test_client().get('/api/heatmap?repo=sws2apps/organized-app&refresh=1')
            self.assertEqual(response.status_code, 200)
            fetch.assert_called_once_with('sws2apps/organized-app', force_refresh=True)
            root = etree.fromstring(response.data)
            for code, count in [('DE', 2), ('NG', 1), ('NE', 1), ('RU', 1)]:
                self.assertEqual(root.xpath(f'//*[@id="{code}"]')[0].get('fill'), get_color(count, 2))

if __name__ == '__main__':
    unittest.main()
