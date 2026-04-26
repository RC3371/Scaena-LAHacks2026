function EmailChart() {
  const chartRef = React.useRef(null);
  const chartInstance = React.useRef(null);

  React.useEffect(() => {
    if (chartRef.current && ChartJS) {
      const ctx = chartRef.current.getContext('2d');
      
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      ChartJS.defaults.color = '#fff';
      ChartJS.defaults.font.family = "'Space Mono', monospace";
      ChartJS.defaults.font.weight = 'bold';

      chartInstance.current = new ChartJS(ctx, {
        type: 'line',
        data: {
          labels: ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'],
          datasets: [
            {
              label: 'Pitches Dropped',
              data: [1200, 1900, 1500, 2200, 1800, 800, 500],
              borderColor: '#00FFFF', // neon cyan
              backgroundColor: 'rgba(0, 255, 255, 0.2)',
              borderWidth: 4,
              tension: 0.4, // Curvy lines for pop feel
              pointBackgroundColor: '#FF00FF',
              pointBorderColor: '#000',
              pointBorderWidth: 2,
              pointRadius: 6,
              pointHoverRadius: 8,
              fill: true
            },
            {
              label: 'Promoter Hype',
              data: [400, 850, 600, 1100, 900, 300, 200],
              borderColor: '#39FF14', // neon green
              borderWidth: 4,
              borderDash: [10, 5],
              tension: 0.4,
              pointBackgroundColor: '#FFFF00',
              pointBorderColor: '#000',
              pointBorderWidth: 2,
              pointRadius: 5,
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              labels: {
                color: '#fff',
                font: { size: 14, family: "'Bungee', cursive" }
              }
            },
            tooltip: {
              backgroundColor: '#FF00FF',
              titleColor: '#fff',
              bodyColor: '#fff',
              titleFont: { family: "'Bungee', cursive" },
              bodyFont: { weight: 'bold' },
              borderColor: '#000',
              borderWidth: 3,
              cornerRadius: 12,
              padding: 10
            }
          },
          scales: {
            y: {
              grid: {
                color: 'rgba(255, 255, 255, 0.1)',
                lineWidth: 2
              },
              beginAtZero: true
            },
            x: {
              grid: {
                color: 'rgba(255, 255, 255, 0.1)',
                lineWidth: 2
              }
            }
          }
        }
      });
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, []);

  return (
    <div className="y2k-panel p-6 h-[400px] flex flex-col bg-[var(--neon-purple)] !border-4 !border-black" data-name="email-chart" data-file="components/EmailChart.js">
      <div className="flex justify-between items-center mb-4 bg-black p-3 rounded-xl border-2 border-[var(--neon-cyan)] shadow-[4px_4px_0px_0px_rgba(0,255,255,1)]">
        <h2 className="text-2xl pixel-text text-[var(--neon-cyan)]">HYPE ANALYTICS</h2>
        <div className="flex space-x-2">
          <button className="text-xs border-2 border-[var(--neon-pink)] text-black bg-[var(--neon-pink)] font-bold rounded-full px-3 py-1 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all">7D</button>
          <button className="text-xs border-2 border-white text-white font-bold rounded-full px-3 py-1 hover:bg-white hover:text-black transition-colors">30D</button>
        </div>
      </div>
      <div className="flex-1 relative w-full h-full bg-black/40 rounded-xl p-4 border-2 border-black">
        <canvas ref={chartRef}></canvas>
      </div>
    </div>
  );
}
