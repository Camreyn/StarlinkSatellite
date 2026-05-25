import { CalendarDays, Pause, Play, RotateCcw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { FactBadge } from '../components/Badge';
import { SectionHeader } from '../components/Layout';
import { ErrorMessage, Loading } from '../components/Loading';
import type { TimelineEvent } from '../types/api';
import { formatDate } from '../utils/format';

const DAY_MS = 24 * 60 * 60 * 1000;

function toDay(value: string) {
  return new Date(`${value.slice(0, 10)}T00:00:00Z`).getTime();
}

function fromDay(value: number) {
  return new Date(value).toISOString().slice(0, 10);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function OrbitPlayback({
  events,
  selectedDate,
  setSelectedDate,
}: {
  events: TimelineEvent[];
  selectedDate: string;
  setSelectedDate: (value: string) => void;
}) {
  const [playing, setPlaying] = useState(false);
  const decayEvents = useMemo(() => events.filter((event) => event.type === 'decay'), [events]);
  const datedEvents = useMemo(() => events.filter((event) => event.date), [events]);
  const minDay = useMemo(() => Math.min(...datedEvents.map((event) => toDay(event.date))), [datedEvents]);
  const maxDay = useMemo(() => Math.max(...datedEvents.map((event) => toDay(event.date))), [datedEvents]);
  const currentDay = clamp(toDay(selectedDate), minDay, maxDay);

  const decayByDate = useMemo(() => {
    const counts = new Map<string, number>();
    for (const event of decayEvents) {
      counts.set(event.date, (counts.get(event.date) ?? 0) + 1);
    }
    return [...counts.entries()]
      .map(([date, count]) => ({ date, count, day: toDay(date) }))
      .sort((a, b) => a.day - b.day);
  }, [decayEvents]);

  const currentDecayCount = decayByDate.find((item) => item.date === selectedDate)?.count ?? 0;
  const decayedSoFar = decayEvents.filter((event) => toDay(event.date) <= currentDay).length;
  const upcoming = decayEvents.filter((event) => toDay(event.date) > currentDay).length;
  const visibleDecayDays = decayByDate.filter((item) => item.day <= currentDay).slice(-52);
  const activeDayEvents = events.filter((event) => event.date === selectedDate);
  const nearbyEvents = events
    .filter((event) => Math.abs(toDay(event.date) - currentDay) <= 14 * DAY_MS)
    .slice(0, 18);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      const nextDay = currentDay + 7 * DAY_MS;
      if (nextDay > maxDay) {
        setPlaying(false);
        setSelectedDate(fromDay(maxDay));
      } else {
        setSelectedDate(fromDay(nextDay));
      }
    }, 450);
    return () => window.clearInterval(timer);
  }, [currentDay, maxDay, playing, setSelectedDate]);

  const progress = maxDay === minDay ? 0 : ((currentDay - minDay) / (maxDay - minDay)) * 100;

  return (
    <section className="mb-5 grid gap-4 rounded border border-zinc-200 bg-white p-4 lg:grid-cols-[minmax(360px,1.1fr)_minmax(320px,0.9fr)]">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold">Orbital Playback</h3>
            <p className="text-sm text-zinc-600">
              Stylized view: dots are event days, not real satellite positions.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              className="focus-ring inline-flex h-9 items-center gap-2 rounded bg-orbit px-3 text-sm text-white"
              onClick={() => setPlaying(!playing)}
            >
              {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {playing ? 'Pause' : 'Play'}
            </button>
            <button
              className="focus-ring inline-flex h-9 items-center gap-2 rounded border border-zinc-300 px-3 text-sm"
              onClick={() => {
                setPlaying(false);
                setSelectedDate(fromDay(minDay));
              }}
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </button>
          </div>
        </div>

        <div className="mt-4 rounded bg-zinc-950 p-4 text-white">
          <svg viewBox="0 0 760 420" className="h-[420px] w-full" role="img" aria-label="Stylized globe and deorbit timeline playback">
            <defs>
              <radialGradient id="earthGlow" cx="42%" cy="35%" r="65%">
                <stop offset="0%" stopColor="#7dd3fc" />
                <stop offset="55%" stopColor="#0f766e" />
                <stop offset="100%" stopColor="#12312d" />
              </radialGradient>
              <linearGradient id="fall" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#fbbf24" />
                <stop offset="100%" stopColor="#be123c" />
              </linearGradient>
            </defs>

            <circle cx="380" cy="210" r="112" fill="url(#earthGlow)" />
            <path d="M300 142 C330 122 350 150 382 132 C424 108 470 134 482 170 C452 164 420 176 406 205 C390 238 330 222 310 260 C282 228 272 174 300 142Z" fill="#d9f99d" opacity="0.55" />
            <path d="M455 235 C500 248 505 294 470 315 C425 300 408 270 425 242 C435 232 444 231 455 235Z" fill="#bbf7d0" opacity="0.45" />

            {[0, 1, 2].map((ring) => (
              <ellipse
                key={ring}
                cx="380"
                cy="210"
                rx={210 + ring * 34}
                ry={64 + ring * 13}
                fill="none"
                stroke={ring === 1 ? '#67e8f9' : '#94a3b8'}
                strokeWidth="1.2"
                opacity={ring === 1 ? 0.48 : 0.28}
                transform={`rotate(${ring * 24 - 20} 380 210)`}
              />
            ))}

            {visibleDecayDays.map((item, index) => {
              const orbit = index % 3;
              const angle = (index * 47 + item.count * 9) * (Math.PI / 180);
              const rx = 210 + orbit * 34;
              const ry = 64 + orbit * 13;
              const rotation = (orbit * 24 - 20) * (Math.PI / 180);
              const x0 = Math.cos(angle) * rx;
              const y0 = Math.sin(angle) * ry;
              const x = 380 + x0 * Math.cos(rotation) - y0 * Math.sin(rotation);
              const y = 210 + x0 * Math.sin(rotation) + y0 * Math.cos(rotation);
              const fresh = Math.abs(item.day - currentDay) < 8 * DAY_MS;
              const radius = Math.min(10, 3 + Math.sqrt(item.count));
              return (
                <g key={item.date}>
                  {fresh ? (
                    <line x1={x} y1={y} x2={380 + (x - 380) * 0.62} y2={210 + (y - 210) * 0.62} stroke="url(#fall)" strokeWidth="2.6" opacity="0.9" />
                  ) : null}
                  <circle cx={fresh ? 380 + (x - 380) * 0.78 : x} cy={fresh ? 210 + (y - 210) * 0.78 : y} r={radius} fill={fresh ? '#fb7185' : '#e5e7eb'} opacity={fresh ? 0.95 : 0.65} />
                </g>
              );
            })}

            <text x="28" y="42" fill="#f8fafc" fontSize="22" fontWeight="700">{selectedDate}</text>
            <text x="28" y="70" fill="#cbd5e1" fontSize="13">Decay/reentry events on this date: {currentDecayCount}</text>
            <text x="28" y="92" fill="#cbd5e1" fontSize="13">Decayed through this point: {decayedSoFar}</text>
            <text x="28" y="114" fill="#cbd5e1" fontSize="13">Later decay records: {upcoming}</text>
          </svg>
        </div>

        <div className="mt-4">
          <input
            aria-label="Timeline playback date"
            type="range"
            min={minDay}
            max={maxDay}
            step={DAY_MS}
            value={currentDay}
            onChange={(event) => {
              setPlaying(false);
              setSelectedDate(fromDay(Number(event.target.value)));
            }}
            className="w-full accent-orbit"
          />
          <div className="mt-1 flex justify-between text-xs text-zinc-500">
            <span>{fromDay(minDay)}</span>
            <span>{Math.round(progress)}%</span>
            <span>{fromDay(maxDay)}</span>
          </div>
        </div>
      </div>

      <aside className="rounded border border-zinc-200 bg-zinc-50 p-4">
        <h3 className="font-semibold">What Is Happening Here</h3>
        <p className="mt-2 text-sm text-zinc-700">
          The globe is intentionally symbolic. It shows the rhythm of public lifecycle events over time, with recent
          decay days falling inward. It is not a claim about exact positions, reentry tracks, or internal causes.
        </p>
        <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
          <div className="rounded border border-zinc-200 bg-white p-3">
            <div className="text-zinc-500">Selected day</div>
            <div className="text-xl font-semibold">{currentDecayCount}</div>
          </div>
          <div className="rounded border border-zinc-200 bg-white p-3">
            <div className="text-zinc-500">So far</div>
            <div className="text-xl font-semibold">{decayedSoFar}</div>
          </div>
          <div className="rounded border border-zinc-200 bg-white p-3">
            <div className="text-zinc-500">Remaining</div>
            <div className="text-xl font-semibold">{upcoming}</div>
          </div>
        </div>
        <h4 className="mt-5 text-sm font-semibold">Events Near Playback Date</h4>
        <div className="mt-2 max-h-[360px] overflow-auto rounded border border-zinc-200 bg-white">
          {(activeDayEvents.length ? activeDayEvents : nearbyEvents).map((event) => (
            <div key={`${event.id}-near`} className="border-b border-zinc-100 p-3 last:border-b-0">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium">{formatDate(event.date)}</span>
                <span className="rounded border border-zinc-300 px-2 py-0.5 text-xs">{event.type}</span>
                {event.fact_vs_inference ? <FactBadge value={event.fact_vs_inference} /> : null}
              </div>
              <p className="mt-1 text-sm text-zinc-700">{event.title}</p>
            </div>
          ))}
        </div>
      </aside>
    </section>
  );
}

export function Timeline() {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState('2024-11-05');

  useEffect(() => {
    api
      .timeline()
      .then((items) => {
        setEvents(items);
        const firstDecay = items.find((event) => event.type === 'decay');
        if (firstDecay) setSelectedDate(firstDecay.date);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading label="Loading timeline" />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div>
      <SectionHeader title="Timeline" />
      <OrbitPlayback events={events} selectedDate={selectedDate} setSelectedDate={setSelectedDate} />
      <div className="rounded border border-zinc-200 bg-white">
        {events.map((event) => (
          <article key={event.id} className="grid gap-3 border-b border-zinc-100 p-4 last:border-b-0 md:grid-cols-[160px_1fr]">
            <div className="flex items-center gap-2 text-sm font-medium text-zinc-700">
              <CalendarDays className="h-4 w-4" aria-hidden="true" />
              {formatDate(event.date)}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-semibold">{event.title}</h3>
                <span className="rounded border border-zinc-300 px-2 py-0.5 text-xs">{event.type}</span>
                {event.fact_vs_inference ? <FactBadge value={event.fact_vs_inference} /> : null}
              </div>
              {event.description ? <p className="mt-1 text-sm text-zinc-600">{event.description}</p> : null}
              {event.source_name ? <p className="mt-1 text-xs text-zinc-500">{event.source_name}</p> : null}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
