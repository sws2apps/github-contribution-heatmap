# GitHub Contributors Heatmap

Embeddable SVG widget that visualizes the geographic distribution of your repository's contributors. Shows all-time contributor data on a world map with country-level heatmap coloring.

## Variants

### Map Light

![Map Light](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=sws2apps/organized-app&variant=map&theme=light)

### Map + List Light

![Map + List Light](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=sws2apps/organized-app&theme=light)

### Map Dark

![Map Dark](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=sws2apps/organized-app&variant=map&theme=dark)

### Map + List Dark

![Map + List Dark](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=sws2apps/organized-app&theme=dark)

_Examples generated for the [sws2apps/organized-app](https://github.com/sws2apps/organized-app) repository._

## Features

- **All-time contributor stats** - Aggregates location data from all contributors
- **World map heatmap** - Visual intensity based on contributor count per country
- **Country leaderboard** - Optional sidebar showing top 10 countries
- **Auto-caching** - 24-hour cache to respect GitHub API rate limits
- **SVG output** - Crisp rendering at any size, works in GitHub READMEs

## Usage

Add this to your README.md:

### Map Light

```markdown
![Contributors Heatmap](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=OWNER/REPO&variant=map&theme=light)
```

### Map + List Light

```markdown
![Contributors Heatmap](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=OWNER/REPO&variant=list&theme=light)
```

### Map Dark

```markdown
![Contributors Heatmap Dark](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=OWNER/REPO&variant=map&theme=dark)
```

### Map + List Dark

```markdown
![Contributors Heatmap Dark](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=OWNER/REPO&variant=list&theme=dark)
```

| Parameter | Type   | Default | Description                                   |
| --------- | ------ | ------- | --------------------------------------------- |
| `repo`    | string | Yes     | GitHub repository (owner/name)                |
| `variant` | string | `list`  | `list` (with leaderboard) or `map` (map only) |
| `theme`   | string | `light` | `light` or `dark`                             |

## Self-Hosting

### Requirements

- Python 3.9+
- GitHub Personal Access Token (for API rate limits)

### Deploy to Vercel

1. Fork this repository
2. Import to [Vercel](https://vercel.com)
3. Add environment variable: `GITHUB_TOKEN` = your token
4. Deploy

### Local Development

```bash
git clone https://github.com/ux-git/github-contribution-heatmap.git
cd github-contribution-heatmap

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export GITHUB_TOKEN=your_token_here
python api/main.py
```

Server runs at `http://localhost:5002`

## API Reference

```
GET /api/heatmap
```

| Parameter | Type   | Required | Description                          |
| --------- | ------ | -------- | ------------------------------------ |
| `repo`    | string | Yes      | GitHub repository (owner/name)       |
| `variant` | string | No       | `list` or `map` (default: `list`)    |
| `theme`   | string | No       | `light` or `dark` (default: `light`) |
| `refresh` | string | No       | Set to `1` to bypass cache           |

## How It Works

1. Fetches all contributors via GitHub API
2. Resolves each contributor's location to a country code
3. Aggregates counts per country
4. Renders SVG with proportional color intensity
5. Caches results for 24 hours

## Limitations

- Only works with public repositories
- Contributor locations are self-reported and optional
- Location resolution uses fuzzy matching (may have edge cases)

## Credits

- Current map: [amCharts Mercator SVG](https://www.amcharts.com/svg-maps/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), modified. Attribution is included in every generated image.
- Prepared geometry is copied unchanged from [`ux-git/contributors-map-widget` at c2314d6](https://github.com/ux-git/contributors-map-widget/blob/c2314d6e02c6734a4832e63bef9e22aff2017e60/data/world-mercator.svg). That repository contains the original asset, preparation script and geometry tests.
- The retained legacy `sirlisko-world-map.svg` is from [sirLisko/world-map-country-shapes](https://github.com/sirLisko/world-map-country-shapes), based on SimpleMaps, MIT by Pareto Software, LLC. It is no longer rendered.

## Validation

```sh
python tests/test_location_resolution.py
python -m unittest discover -s tests -p 'test_rendering.py'
```

Pushing main triggers the connected Vercel deployment. Verify the production response contains `data-map-version="mercator-v2"`; a successful push alone does not prove deployment. The prior server release is `6a729b6e2a59cd97781ad6ed635c6e6c0aaaa4b3`; rollback can be made with a revert commit.
