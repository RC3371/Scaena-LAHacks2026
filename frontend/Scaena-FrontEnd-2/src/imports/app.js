class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--dark-bg)] text-white">
          <div className="y2k-panel p-8 text-center bg-[var(--neon-pink)] text-black shadow-[8px_8px_0px_0px_rgba(0,255,255,1)]">
            <h1 className="text-4xl font-bold text-black mb-4 pixel-text">MAJOR BUZZKILL!</h1>
            <p className="text-black font-bold mb-6">The DJ dropped the track. Something went wrong.</p>
            <button onClick={() => window.location.reload()} className="y2k-btn !bg-[var(--neon-cyan)]">
              REMIX & RELOAD
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  try {
    return (
      <div className="flex h-screen overflow-hidden" data-name="app" data-file="app.js">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden relative">
          <Header />
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-transparent p-6">
            <div className="max-w-7xl mx-auto space-y-6">
              {/* Top Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard title="PITCHES SENT" value="14,092" icon="mic" trend="+12.5%" color="pink" />
                <StatCard title="PROMOTER REPLIES" value="18.4%" icon="message-square" trend="+4.2%" color="cyan" />
                <StatCard title="GIGS BOOKED" value="47" icon="ticket" trend="+18.1%" color="green" />
              </div>
              
              {/* Main Content Area */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <EmailChart />
                </div>
                <div className="lg:col-span-1">
                  <AgentList />
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  } catch (error) {
    console.error('App component error:', error);
    return null;
  }
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);