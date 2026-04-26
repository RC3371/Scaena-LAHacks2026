import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { MapPin, DollarSign, CheckCircle, ExternalLink, ChevronRight } from "lucide-react";
import { client } from "../api/client";

const PROFESSIONS = [
  { value: "comedian", label: "Comedian" },
  { value: "musician", label: "Musician" },
  { value: "rapper", label: "Rapper" },
  { value: "speaker", label: "Speaker / MC" },
  { value: "dj", label: "DJ" },
  { value: "singer", label: "Singer" },
  { value: "band", label: "Band" },
  { value: "dancer", label: "Dancer / Performer" },
  { value: "other", label: "Other" },
];

const VENUE_TYPES = [
  "College / University", "Music Festival", "Music Venue", "Bar / Lounge",
  "Campus Concert", "Showcase", "Nightlife", "Outdoor Stage",
  "Private Event", "Theater", "Hotel", "Conference / Summit",
];

const inputCls = "w-full bg-black border-4 border-zinc-800 rounded-xl px-4 py-3 text-[15px] text-white placeholder-zinc-600 focus:outline-none focus:border-[var(--color-neon-purple)] transition-all font-sans";
const labelCls = "text-[12px] font-bold text-zinc-400 uppercase tracking-widest font-[var(--font-space)] mb-2 block";

export function Onboarding() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [googleLinked, setGoogleLinked] = useState(
    () => localStorage.getItem("scaena_google_linked") === "true"
  );
  const [googleEmail, setGoogleEmail] = useState("");
  const [gmailConfigured, setGmailConfigured] = useState(false);
  const [gmailSyncEnabled, setGmailSyncEnabled] = useState(false);
  const [existingId, setExistingId] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    type: "musician",
    genre: "",
    location: "",
    current_rate: "",
    experience_years: "",
    social_followers: "",
    instagram: "",
    tiktok: "",
    youtube: "",
    website: "",
    objectives: "",
    preferred_venues: [] as string[],
  });

  useEffect(() => {
    (async () => {
      try {
        if (new URLSearchParams(window.location.search).get("gmail") === "connected") {
          localStorage.setItem("scaena_google_linked", "true");
          setGoogleLinked(true);
          window.history.replaceState({}, "", window.location.pathname);
        }
        const entertainers = await client.entertainers.active();
        if (entertainers.length) {
          const ent = entertainers[0];
          setExistingId(ent.id);
          try {
            const gmail = await client.gmail.status(ent.id);
            setGmailConfigured(Boolean(gmail.configured));
            setGoogleLinked(Boolean(gmail.connected) || localStorage.getItem("scaena_google_linked") === "true");
            setGoogleEmail(gmail.email || "");
            setGmailSyncEnabled(Boolean(gmail.read_sync_enabled));
          } catch {}
          let links: Record<string, string> = {};
          try { links = JSON.parse(ent.links || "{}"); } catch {}
          setForm({
            name: ent.name || "",
            type: ent.type || "musician",
            genre: ent.genre || "",
            location: ent.location || "",
            current_rate: ent.current_rate ? String(ent.current_rate) : "",
            experience_years: ent.experience_years ? String(ent.experience_years) : "",
            social_followers: ent.social_followers ? String(ent.social_followers) : "",
            instagram: links.instagram || "",
            tiktok: links.tiktok || "",
            youtube: links.youtube || "",
            website: links.website || "",
            objectives: ent.highlights || "",
            preferred_venues: links.preferred_venues ? JSON.parse(links.preferred_venues) : [],
          });
        }
      } catch {}
    })();
  }, []);

  const set = (field: string, value: string) => setForm((f) => ({ ...f, [field]: value }));

  const toggleVenue = (v: string) => {
    setForm((f) => ({
      ...f,
      preferred_venues: f.preferred_venues.includes(v)
        ? f.preferred_venues.filter((x) => x !== v)
        : [...f.preferred_venues, v],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    const links = JSON.stringify({
      instagram: form.instagram,
      tiktok: form.tiktok,
      youtube: form.youtube,
      website: form.website,
      preferred_venues: JSON.stringify(form.preferred_venues),
    });
    const payload = {
      name: form.name,
      type: form.type,
      genre: form.genre,
      location: form.location,
      current_rate: form.current_rate ? parseFloat(form.current_rate) : undefined,
      experience_years: form.experience_years ? parseInt(form.experience_years) : undefined,
      social_followers: form.social_followers ? parseInt(form.social_followers) : undefined,
      highlights: form.objectives,
      links,
      outreach_mode: "manual_approve" as const,
    };
    try {
      if (existingId) {
        await client.entertainers.update(existingId, payload);
      } else {
        await client.entertainers.create(payload);
      }
      localStorage.setItem("scaena_onboarded", "true");
      navigate("/");
    } catch (e) {
      console.error(e);
    }
    setSaving(false);
  };

  const handleLinkGoogle = async () => {
    if (!existingId) {
      window.alert("Save the profile first, then connect Gmail.");
      return;
    }
    try {
      const { auth_url } = await client.gmail.authUrl(existingId, "/onboarding?gmail=connected");
      window.location.href = auth_url;
    } catch (error: any) {
      const detail = error?.response?.data?.detail || "Gmail OAuth is not configured yet.";
      window.alert(detail);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-dark-bg)] bg-[radial-gradient(rgba(255,255,255,0.04)_2px,transparent_2px)] bg-[length:30px_30px] flex flex-col items-center justify-start py-12 px-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <div className="flex items-center justify-center gap-3 mb-4">
          <svg viewBox="0 0 100 100" className="w-10 h-10" fill="none" stroke="var(--color-neon-purple)" strokeWidth="5">
            <circle cx="50" cy="50" r="45" />
            <ellipse cx="50" cy="50" rx="18" ry="45" />
            <ellipse cx="50" cy="50" rx="45" ry="18" />
            <line x1="5" y1="50" x2="95" y2="50" />
            <line x1="50" y1="5" x2="50" y2="95" />
          </svg>
          <h1 className="text-4xl font-[var(--font-bungee)] text-white tracking-widest">SCAENA OS</h1>
        </div>
        <p className="text-zinc-400 font-[var(--font-space)] text-[14px] uppercase tracking-widest">Set up your agent profile to begin</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* Left: Identity */}
        <div className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-7 shadow-[6px_6px_0px_0px_var(--color-neon-purple)] flex flex-col gap-6">
          <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-purple)] border-b-4 border-black pb-4">IDENTITY</h2>

          <div>
            <label className={labelCls}>Your Name</label>
            <input className={inputCls} placeholder="Your stage name" value={form.name} onChange={(e) => set("name", e.target.value)} />
          </div>

          <div>
            <label className={labelCls}>Profession</label>
            <select
              className={`${inputCls} cursor-pointer`}
              value={form.type}
              onChange={(e) => set("type", e.target.value)}
            >
              {PROFESSIONS.map((p) => (
                <option key={p.value} value={p.value} className="bg-black">{p.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelCls}>Genre / Style</label>
            <input className={inputCls} placeholder="e.g. Hip-hop / College rap" value={form.genre} onChange={(e) => set("genre", e.target.value)} />
          </div>

          <div className="border-t-4 border-black pt-6">
            <h3 className="text-[14px] font-[var(--font-bungee)] text-zinc-300 mb-4">SOCIALS</h3>
            <div className="space-y-3">
              {[
                { key: "instagram", label: "Instagram", placeholder: "@yourhandle" },
                { key: "tiktok", label: "TikTok", placeholder: "@yourhandle" },
                { key: "youtube", label: "YouTube", placeholder: "channel URL" },
                { key: "website", label: "Website", placeholder: "yoursite.com" },
              ].map(({ key, label, placeholder }) => (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-[12px] font-bold text-zinc-500 font-[var(--font-space)] w-24 uppercase">{label}</span>
                  <input
                    className="flex-1 bg-black border-2 border-zinc-800 rounded-lg px-3 py-2 text-[13px] text-white placeholder-zinc-700 focus:outline-none focus:border-[var(--color-neon-purple)] transition-all font-sans"
                    placeholder={placeholder}
                    value={(form as any)[key]}
                    onChange={(e) => set(key, e.target.value)}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="border-t-4 border-black pt-6">
            <label className={labelCls}>Google Account (for sending emails)</label>
            {googleLinked ? (
              <div className="flex items-center gap-3 bg-black border-4 border-[var(--color-neon-green)] px-5 py-3 rounded-full w-fit">
                <CheckCircle size={18} className="text-[var(--color-neon-green)]" strokeWidth={3} />
                <span className="text-[var(--color-neon-green)] font-bold text-[14px] font-[var(--font-space)]">
                  {googleEmail ? `GMAIL CONNECTED: ${googleEmail}` : "GMAIL CONNECTED"}
                </span>
                {!gmailSyncEnabled && (
                  <button
                    onClick={handleLinkGoogle}
                    className="ml-2 bg-white text-black border-2 border-black px-3 py-1 rounded-full text-[11px] font-bold"
                  >
                    ENABLE REPLY SYNC
                  </button>
                )}
              </div>
            ) : (
              <button
                onClick={handleLinkGoogle}
                className="flex items-center gap-3 bg-white text-black border-4 border-black px-5 py-3 rounded-full font-bold text-[14px] hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all font-[var(--font-space)] disabled:opacity-50 disabled:pointer-events-none"
                disabled={!gmailConfigured}
              >
                <ExternalLink size={18} strokeWidth={3} />
                {gmailConfigured ? "LINK GMAIL ACCOUNT" : "GMAIL NOT CONFIGURED"}
              </button>
            )}
          </div>
        </div>

        {/* Right: Specifications */}
        <div className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-7 shadow-[6px_6px_0px_0px_var(--color-neon-purple)] flex flex-col gap-6">
          <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-purple)] border-b-4 border-black pb-4">SPECIFICATIONS</h2>

          <div className="flex gap-4">
            <div className="flex-1">
              <label className={labelCls}><MapPin size={12} className="inline mr-1" />Location</label>
              <input className={inputCls} placeholder="Los Angeles, CA" value={form.location} onChange={(e) => set("location", e.target.value)} />
            </div>
            <div className="w-36">
              <label className={labelCls}><DollarSign size={12} className="inline mr-1" />Min Rate / Show</label>
              <input className={inputCls} type="number" placeholder="350" value={form.current_rate} onChange={(e) => set("current_rate", e.target.value)} />
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <label className={labelCls}>Years Experience</label>
              <input className={inputCls} type="number" placeholder="2" value={form.experience_years} onChange={(e) => set("experience_years", e.target.value)} />
            </div>
            <div className="flex-1">
              <label className={labelCls}>Social Followers</label>
              <input className={inputCls} type="number" placeholder="4800" value={form.social_followers} onChange={(e) => set("social_followers", e.target.value)} />
            </div>
          </div>

          <div>
            <label className={labelCls}>Preferred Venue Types</label>
            <div className="flex flex-wrap gap-2 mt-1">
              {VENUE_TYPES.map((v) => {
                const active = form.preferred_venues.includes(v);
                return (
                  <button
                    key={v}
                    onClick={() => toggleVenue(v)}
                    className={`px-3 py-1.5 rounded-full text-[12px] font-bold border-2 transition-all font-[var(--font-space)] uppercase ${
                      active
                        ? "bg-[var(--color-neon-purple)] text-black border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
                        : "bg-black text-zinc-400 border-zinc-700 hover:border-[var(--color-neon-purple)] hover:text-white"
                    }`}
                  >
                    {v}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex-1">
            <label className={labelCls}>Objectives &amp; Growth Targets</label>
            <textarea
              className={`${inputCls} resize-none`}
              rows={5}
              placeholder="e.g. Earn at least $10k, reach 1000+ people, and book college campuses, music festivals, music shows, and bars..."
              value={form.objectives}
              onChange={(e) => set("objectives", e.target.value)}
            />
          </div>
        </div>
      </motion.div>

      {/* CTA */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="mt-8 flex items-center gap-6"
      >
        <button
          onClick={handleSave}
          disabled={!form.name || saving}
          className="flex items-center gap-3 px-10 py-4 bg-[var(--color-neon-purple)] text-white border-4 border-black text-[18px] font-[var(--font-bungee)] rounded-2xl hover:-translate-y-1 hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] transition-all disabled:opacity-40 disabled:pointer-events-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
        >
          {saving ? "SAVING..." : "LAUNCH SCAENA OS"}
          <ChevronRight size={22} strokeWidth={3} />
        </button>
        <button
          onClick={() => { localStorage.setItem("scaena_onboarded", "true"); navigate("/"); }}
          className="text-zinc-500 text-[13px] font-[var(--font-space)] underline hover:text-zinc-300 transition-colors uppercase"
        >
          Skip for now
        </button>
      </motion.div>
    </div>
  );
}
