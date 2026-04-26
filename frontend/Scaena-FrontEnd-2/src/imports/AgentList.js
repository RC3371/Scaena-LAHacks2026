function AgentList() {
  const agents = [
    { id: 'HB-01', name: 'Gig_Hustler', status: 'HUSTLING', tasks: 124, type: 'Venue Pitcher', icon: 'zap' },
    { id: 'HB-02', name: 'A&R_Scout', status: 'HUSTLING', tasks: 89, type: 'Label Outreach', icon: 'mic' },
    { id: 'HB-03', name: 'Podcast_Pal', status: 'CHILLING', tasks: 0, type: 'Interview Booker', icon: 'coffee' },
    { id: 'HB-04', name: 'Hype_Machine', status: 'HUSTLING', tasks: 312, type: 'Playlist Pitcher', icon: 'flame' },
  ];

  return (
    <div className="y2k-panel h-full flex flex-col !bg-[var(--neon-yellow)] !shadow-[6px_6px_0px_0px_rgba(255,0,255,1)]" data-name="agent-list" data-file="components/AgentList.js">
      <div className="p-4 border-b-4 border-black bg-[var(--neon-pink)] flex justify-between items-center rounded-t-xl">
        <h2 className="text-2xl pixel-text text-black">HYPE BOTS</h2>
        <button className="y2k-btn !py-1 !text-xs !bg-white !text-black !shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:!bg-[var(--neon-cyan)]">
          + DROP BOT
        </button>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {agents.map((agent) => (
          <div key={agent.id} className="border-4 border-black p-3 rounded-xl hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all group cursor-pointer bg-white text-black">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center space-x-2">
                <div className={`icon-${agent.icon} text-[var(--neon-purple)] text-xl`}></div>
                <span className="font-bold text-black text-sm uppercase">{agent.name}</span>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border-2 border-black shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] ${
                agent.status === 'HUSTLING' 
                  ? 'bg-[var(--neon-green)] text-black' 
                  : 'bg-gray-300 text-black'
              }`}>
                {agent.status}
              </span>
            </div>
            
            <div className="text-xs text-gray-600 font-bold mb-3 bg-gray-100 p-1 rounded inline-block">{agent.type}</div>
            
            <div className="flex justify-between items-center text-xs font-bold">
              <span className="text-gray-500 bg-gray-100 px-1 rounded">ID: {agent.id}</span>
              <span className="text-[var(--neon-purple)] bg-[var(--neon-cyan)] px-2 py-0.5 rounded-full border border-black shadow-[1px_1px_0px_0px_rgba(0,0,0,1)]">{agent.tasks} pitches/hr</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
