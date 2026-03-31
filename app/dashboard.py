# ANALYTICS
from __future__ import annotations


def get_dashboard_html() -> str:
  return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>PromptReviewEnv Analytics</title>
  <link href=\"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap\" rel=\"stylesheet\">
  <script src=\"https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js\"></script>
  <script src=\"https://unpkg.com/react@18/umd/react.production.min.js\"></script>
  <script src=\"https://unpkg.com/react-dom@18/umd/react-dom.production.min.js\"></script>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7fb;
      --bg-accent: #e3e7ff;
      --text: #161925;
      --card: #ffffff;
      --muted: #5b6472;
      --accent: #2b5cff;
      --accent-2: #00a676;
      --accent-3: #f39c12;
      --accent-4: #ff6b6b;
      --chart-1: #2b5cff;
      --chart-2: #00a676;
      --chart-3: #f39c12;
      --chart-4: #ff6b6b;
      --grid: rgba(22, 25, 37, 0.12);
      --glow: rgba(43, 92, 255, 0.18);
    }
    [data-theme=\"dark\"] {
      color-scheme: dark;
      --bg: #0c0f16;
      --bg-accent: #1b2235;
      --text: #f5f7ff;
      --card: #151b27;
      --muted: #9aa5b4;
      --accent: #7aa2ff;
      --accent-2: #4fd1a5;
      --accent-3: #f7c86b;
      --accent-4: #ff7b6b;
      --chart-1: #7aa2ff;
      --chart-2: #4fd1a5;
      --chart-3: #f7c86b;
      --chart-4: #ff7b6b;
      --grid: rgba(245, 247, 255, 0.15);
      --glow: rgba(122, 162, 255, 0.2);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Space Grotesk", sans-serif;
      background: radial-gradient(circle at top, var(--bg-accent), var(--bg));
      color: var(--text);
      min-height: 100vh;
    }
    header {
      padding: 24px 40px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--grid);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    header h1 {
      margin: 0;
      font-size: 22px;
      letter-spacing: 0.6px;
    }
    header .subtitle {
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 1px;
      text-transform: uppercase;
    }
    header button {
      background: var(--card);
      border: 1px solid var(--grid);
      color: var(--text);
      padding: 8px 14px;
      border-radius: 999px;
      cursor: pointer;
    }
    .container {
      padding: 28px 40px 60px;
      max-width: 1280px;
      margin: 0 auto;
    }
    .hero {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 24px;
    }
    .hero .title {
      font-size: 28px;
      font-weight: 700;
    }
    .hero .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 14px;
      border-radius: 999px;
      background: var(--card);
      border: 1px solid var(--grid);
      font-size: 12px;
      color: var(--muted);
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 18px;
      margin-bottom: 24px;
    }
    .card {
      background: var(--card);
      border-radius: 18px;
      padding: 16px;
      border: 1px solid rgba(0, 0, 0, 0.04);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.12);
      position: relative;
      overflow: hidden;
    }
    .card::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(120deg, transparent, var(--glow), transparent);
      opacity: 0.35;
      transform: translateX(-120%);
      transition: transform 0.9s ease;
    }
    .card:hover::after {
      transform: translateX(120%);
    }
    .card h3 {
      margin: 0 0 10px 0;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 1.2px;
    }
    .card .value {
      font-size: 28px;
      font-weight: 600;
    }
    .card .delta {
      font-size: 12px;
      color: var(--muted);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
    }
    .chart-card {
      min-height: 340px;
    }
    canvas {
      width: 100% !important;
      height: 260px !important;
    }
    .roi-panel {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .roi-input {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .roi-input input[type=range] {
      flex: 1;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--muted);
      margin-top: 8px;
    }
    .fade-in {
      animation: fadeInUp 0.6s ease forwards;
      opacity: 0;
      transform: translateY(8px);
    }
    @keyframes fadeInUp {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <div class=\"subtitle\">PromptReviewEnv / Analytics</div>
      <h1>Multi-agent Quality Observatory</h1>
    </div>
    <button id=\"themeToggle\">Toggle theme</button>
  </header>
  <div id=\"root\"></div>

  <script>
    const { useEffect, useRef, useState } = React;

    function cssVar(name) {
      return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    function buildHistogram(scores) {
      const bins = new Array(10).fill(0);
      scores.forEach(score => {
        const idx = Math.min(9, Math.floor(score * 10));
        bins[idx] += 1;
      });
      return bins;
    }

    function DashboardApp() {
      const [summary, setSummary] = useState(null);
      const [baselineCost, setBaselineCost] = useState(0.15);
      const [theme, setTheme] = useState(document.documentElement.getAttribute('data-theme') || 'light');

      const chartsRef = useRef({});
      const scoreRef = useRef(null);
      const costRef = useRef(null);
      const stepsRef = useRef(null);
      const roiRef = useRef(null);

      useEffect(() => {
        const toggle = document.getElementById('themeToggle');
        toggle.onclick = () => {
          const next = theme === 'dark' ? 'light' : 'dark';
          document.documentElement.setAttribute('data-theme', next);
          setTheme(next);
        };
      }, [theme]);

      useEffect(() => {
        let active = true;
        async function fetchSummary() {
          try {
            const response = await fetch('/analytics/summary');
            const data = await response.json();
            if (active) {
              setSummary(data);
            }
          } catch (err) {
            console.error('Failed to fetch analytics summary', err);
          }
        }
        fetchSummary();
        const interval = setInterval(fetchSummary, 30000);
        return () => {
          active = false;
          clearInterval(interval);
        };
      }, []);

      useEffect(() => {
        if (!summary) {
          return;
        }

        const tasks = Object.keys(summary.by_task || {});
        const scores = [];
        const costs = [];
        const avgSteps = [];

        tasks.forEach(task => {
          const entry = summary.by_task[task];
          costs.push(entry.total_cost || 0);
          avgSteps.push(entry.avg_steps || 0);
          if (Array.isArray(entry.scores)) {
            entry.scores.forEach(value => scores.push(value));
          }
        });

        const histogram = buildHistogram(scores);
        const histogramLabels = histogram.map((_, i) => `${i / 10}-${(i + 1) / 10}`);

        const colors = {
          primary: cssVar('--chart-1'),
          secondary: cssVar('--chart-2'),
          tertiary: cssVar('--chart-3'),
          danger: cssVar('--chart-4'),
          grid: cssVar('--grid'),
          text: cssVar('--text'),
        };

        const baseline = (summary.total_episodes || 0) * baselineCost;

        function upsertChart(key, canvas, config) {
          if (!canvas) {
            return;
          }
          if (chartsRef.current[key]) {
            chartsRef.current[key].data = config.data;
            chartsRef.current[key].options = config.options;
            chartsRef.current[key].update();
          } else {
            chartsRef.current[key] = new Chart(canvas, config);
          }
        }

        upsertChart('histogram', scoreRef.current, {
          type: 'bar',
          data: {
            labels: histogramLabels,
            datasets: [{
              label: 'Episodes',
              data: histogram,
              backgroundColor: colors.primary,
            }],
          },
          options: {
            responsive: true,
            scales: {
              x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
              y: { grid: { color: colors.grid }, ticks: { color: colors.text } },
            },
            plugins: { legend: { labels: { color: colors.text } } },
          },
        });

        upsertChart('cost', costRef.current, {
          type: 'bar',
          data: {
            labels: tasks,
            datasets: [{
              label: 'Cost (USD)',
              data: costs,
              backgroundColor: colors.secondary,
            }],
          },
          options: {
            responsive: true,
            scales: {
              x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
              y: { grid: { color: colors.grid }, ticks: { color: colors.text } },
            },
            plugins: { legend: { labels: { color: colors.text } } },
          },
        });

        upsertChart('steps', stepsRef.current, {
          type: 'line',
          data: {
            labels: tasks,
            datasets: [{
              label: 'Avg Steps',
              data: avgSteps,
              borderColor: colors.tertiary,
              backgroundColor: 'transparent',
              tension: 0.35,
            }],
          },
          options: {
            responsive: true,
            scales: {
              x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
              y: { grid: { color: colors.grid }, ticks: { color: colors.text } },
            },
            plugins: { legend: { labels: { color: colors.text } } },
          },
        });

        const roiLabels = ['Human Baseline', 'Actual Spend', 'Saved'];
        const roiValues = [baseline, summary.total_cost || 0, summary.cost_saved || 0];

        upsertChart('roi', roiRef.current, {
          type: 'bar',
          data: {
            labels: roiLabels,
            datasets: [{
              label: 'USD',
              data: roiValues,
              backgroundColor: [colors.primary, colors.danger, colors.secondary],
            }],
          },
          options: {
            responsive: true,
            scales: {
              x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
              y: { grid: { color: colors.grid }, ticks: { color: colors.text } },
            },
            plugins: { legend: { labels: { color: colors.text } } },
          },
        });
      }, [summary, baselineCost, theme]);

      const totalEpisodes = summary ? summary.total_episodes || 0 : 0;
      const avgScore = summary ? summary.avg_score || 0 : 0;
      const totalCost = summary ? summary.total_cost || 0 : 0;
      const costSaved = summary ? summary.cost_saved || 0 : 0;
      const baseline = totalEpisodes * baselineCost;
      const roi = baseline > 0 ? (costSaved / baseline) * 100 : 0;

      const e = React.createElement;

      return e(
        'div',
        { className: 'container' },
        e('section', { className: 'hero' },
          e('div', null,
            e('div', { className: 'title fade-in', style: { animationDelay: '0.1s' } }, 'Analytics Dashboard'),
            e('div', { className: 'badge' }, 'Auto-refreshing every 30s')
          ),
          e('div', { className: 'pill fade-in', style: { animationDelay: '0.2s' } }, 'Live metrics from /analytics/summary')
        ),
        e('section', { className: 'metrics' },
          e('div', { className: 'card fade-in', style: { animationDelay: '0.1s' } },
            e('h3', null, 'Total Episodes'),
            e('div', { className: 'value' }, totalEpisodes)
          ),
          e('div', { className: 'card fade-in', style: { animationDelay: '0.2s' } },
            e('h3', null, 'Average Score'),
            e('div', { className: 'value' }, avgScore.toFixed(2)),
            e('div', { className: 'delta' }, 'Grader composite mean')
          ),
          e('div', { className: 'card fade-in', style: { animationDelay: '0.3s' } },
            e('h3', null, 'Total Cost (USD)'),
            e('div', { className: 'value' }, `$${totalCost.toFixed(2)}`),
            e('div', { className: 'delta' }, 'OpenAI + tools usage')
          ),
          e('div', { className: 'card fade-in', style: { animationDelay: '0.4s' } },
            e('h3', null, 'ROI %'),
            e('div', { className: 'value' }, `${roi.toFixed(1)}%`),
            e('div', { className: 'delta' }, `$${costSaved.toFixed(2)} saved`)
          )
        ),
        e('section', { className: 'grid' },
          e('div', { className: 'card chart-card fade-in', style: { animationDelay: '0.1s' } },
            e('h3', null, 'Score Distribution'),
            e('canvas', { ref: scoreRef })
          ),
          e('div', { className: 'card chart-card fade-in', style: { animationDelay: '0.2s' } },
            e('h3', null, 'Cost per Task'),
            e('canvas', { ref: costRef })
          ),
          e('div', { className: 'card chart-card fade-in', style: { animationDelay: '0.3s' } },
            e('h3', null, 'Average Steps'),
            e('canvas', { ref: stepsRef })
          ),
          e('div', { className: 'card chart-card fade-in', style: { animationDelay: '0.4s' } },
            e('h3', null, 'ROI Calculator'),
            e('div', { className: 'roi-panel' },
              e('div', { className: 'roi-input' },
                e('span', null, 'Human baseline'),
                e('input', {
                  type: 'range',
                  min: '0.05',
                  max: '0.5',
                  step: '0.01',
                  value: baselineCost,
                  onChange: (evt) => setBaselineCost(parseFloat(evt.target.value)),
                }),
                e('strong', null, `$${baselineCost.toFixed(2)}`)
              ),
              e('canvas', { ref: roiRef })
            )
          )
        )
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(DashboardApp));
  </script>
</body>
</html>"""
