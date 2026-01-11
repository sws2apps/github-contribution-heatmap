# GitHub Contribution Map

Embeddable SVG widget that visualizes the geographic distribution of your repository's contributors. Shows all-time contributor data on a world map with country-level heatmap coloring.

## Example

![Contribution Map Example](https://github-contribution-heatmap.vercel.app/api/heatmap?repo=sws2apps/organized-app&variant=list)

*Example generated for the [sws2apps/organized-app](https://github.com/sws2apps/organized-app) repository.*

## Features

- **All-time contributor stats** - Aggregates location data from all contributors
- **World map heatmap** - Visual intensity based on contributor count per country
- **Country leaderboard** - Optional sidebar showing top 10 countries
- **Auto-caching** - 1-hour cache to respect GitHub API rate limits
- **SVG output** - Crisp rendering at any size, works in GitHub READMEs

## Usage

Add this to your README.md:

```markdown
![Contributors](https://your-deployment.vercel.app/api/heatmap?repo=OWNER/REPO)
```

### Variants

| Variant | Parameter | Description |
|---------|-----------|-------------|
| Map only | `variant=map` (default) | World map with heatmap coloring |
| Map + List | `variant=list` | Map with top 10 countries sidebar |

```markdown
<!-- Map with country list -->
![Contributors](https://your-deployment.vercel.app/api/heatmap?repo=OWNER/REPO&variant=list)
```

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
git clone https://github.com/ux-git/github-contribution-map.git
cd github-contribution-map

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

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `repo` | string | Yes | GitHub repository (owner/name) |
| `variant` | string | No | `map` or `list` (default: `map`) |
| `refresh` | string | No | Set to `1` to bypass cache |

## How It Works

1. Fetches all contributors via GitHub API
2. Resolves each contributor's location to a country code
3. Aggregates counts per country
4. Renders SVG with proportional color intensity
5. Caches results for 1 hour

## Limitations

- Only works with public repositories
- Contributor locations are self-reported and optional
- Location resolution uses fuzzy matching (may have edge cases)

## Credits

- Map data source: [sirLisko/world-map-country-shapes](https://github.com/sirLisko/world-map-country-shapes) (based on [SimpleMaps.com](https://simplemaps.com/resources/svg-world))
- Original SVG licensed under MIT by Pareto Software, LLC.

## License

MIT
