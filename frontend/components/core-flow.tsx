'use client'

import { useEffect, useState } from 'react'
import { ArrowRight, Award, BookOpen, Check, ChevronLeft, Compass, House, LogOut, MessageCircle, Search, Settings, Users } from 'lucide-react'
import { api, ApiError, clearToken, getToken, messageOf, post, setToken, type AssessmentDetail, type AssessmentSummary, type Attempt, type ExchangeItem, type Match, type Me, type Person, type Progress } from '@/lib/api'

type Route = '/' | '/login' | '/register' | '/onboarding' | '/dashboard' | '/discover' | '/assessments' | '/exchange' | '/sessions' | '/progress' | '/profile'

function navigate(path: string) { window.history.pushState({}, '', path); window.dispatchEvent(new PopStateEvent('popstate')) }

function useLoad<T>(load: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [tick, setTick] = useState(0)
  useEffect(() => {
    let live = true
    setLoading(true)
    load().then(result => { if (live) { setData(result); setError('') } }).catch(err => { if (live) setError(messageOf(err)) }).finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [...deps, tick])
  return { data, error, loading, reload: () => setTick(t => t + 1) }
}

function Notice({ error }: { error: string }) { return error ? <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null }

function Redirect({ to }: { to: string }) { useEffect(() => navigate(to), [to]); return null }

export default function CoreFlow() {
  const [route, setRoute] = useState<Route>('/')
  const [me, setMe] = useState<Me | null>(null)
  const [ready, setReady] = useState(false)
  const refresh = () => api<Me>('/users/me').then(setMe).catch(() => undefined)
  useEffect(() => {
    setRoute(window.location.pathname as Route)
    const onPop = () => setRoute(window.location.pathname as Route)
    window.addEventListener('popstate', onPop)
    if (getToken()) api<Me>('/users/me').then(setMe).catch(() => clearToken()).finally(() => setReady(true))
    else setReady(true)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  if (!ready) return null
  if (route === '/') return <Landing />
  if (route === '/login' || route === '/register') return <Auth mode={route.slice(1) as 'login' | 'register'} onDone={(user, isNew) => { setMe(user); navigate(isNew ? '/onboarding' : '/dashboard') }} />
  if (!me) return <Redirect to="/login" />
  if (route === '/onboarding') return <Onboarding me={me} onSaved={user => { setMe(user); navigate('/dashboard') }} />
  return <Shell route={route} me={me} onNavigate={navigate} onLogout={() => { clearToken(); setMe(null); navigate('/') }}><Routes route={route} me={me} refresh={refresh} onSaved={setMe} /></Shell>
}

function Button({ children, onClick, variant = 'primary', type = 'button' }: { children: React.ReactNode; onClick?: () => void; variant?: 'primary' | 'outline' | 'text'; type?: 'button' | 'submit' }) { return <button type={type} onClick={onClick} className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2f7651] ${variant === 'primary' ? 'bg-[#173b2b] text-white hover:bg-[#24563d]' : variant === 'outline' ? 'border border-[#d8d7cf] bg-transparent text-[#26352d] hover:bg-[#f2f1eb]' : 'text-[#49745d] hover:text-[#173b2b]'}`}>{children}</button> }
function Logo() { return <button onClick={() => navigate('/')} className="flex items-center gap-2.5 font-semibold tracking-tight"><span className="grid size-8 place-items-center rounded-lg bg-[#173b2b] text-sm text-[#f8f5ec]">S</span><span>skillswap</span></button> }
function Avatar({ initials }: { initials: string }) { return <span className="grid size-10 shrink-0 place-items-center rounded-full bg-[#dcece0] text-xs font-semibold text-[#173b2b]">{initials}</span> }

function Landing() { return <div className="min-h-screen bg-[#f8f7f2]"><header className="flex items-center justify-between px-6 py-5 md:px-12"><Logo /><button onClick={() => navigate('/login')} className="text-sm font-medium text-[#49745d]">Already have an account? <span className="underline">Log in</span></button></header><main className="mx-auto grid max-w-6xl items-center gap-12 px-6 pb-20 pt-12 md:grid-cols-[1fr_.8fr] md:px-12 md:pt-20"><section><p className="eyebrow">A better way to learn together</p><h1 className="mt-5 max-w-xl text-5xl font-semibold leading-[1.06] tracking-[-0.04em] text-[#173b2b] md:text-7xl">Learn a skill.<br /><span className="text-[#73947a]">Share what you know.</span><br />Grow together.</h1><p className="mt-7 max-w-lg text-lg leading-8 text-[#66736b]">Find people who can teach you what you want to learn, and share your own knowledge in return.</p><div className="mt-9 flex flex-wrap gap-3"><Button onClick={() => navigate('/register')}>Find your learning partner <ArrowRight /></Button><Button variant="outline" onClick={() => navigate('/login')}>Log in</Button></div></section><div className="rounded-2xl border border-[#d8d7cf] bg-[#e9f0e6] p-6"><p className="eyebrow">A skill exchange</p><div className="my-10 flex items-center justify-center gap-6"><Avatar initials="AM" /><ArrowRight className="text-[#173b2b]" /><Avatar initials="RM" /></div><p className="rounded-xl bg-[#f8f7f2] p-4 text-sm text-[#66736b]">Real people. Shared goals. No awkward networking.</p></div></main></div> }

function Page({ eyebrow, title, subtitle, children }: { eyebrow: string; title: string; subtitle: string; children: React.ReactNode }) { return <div className="mx-auto max-w-5xl"><p className="eyebrow">{eyebrow}</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-[#173b2b]">{title}</h1><p className="mt-2 text-[#66736b]">{subtitle}</p>{children}</div> }
function Card({ title, children }: { title: string; children: React.ReactNode }) { return <section className="mt-6 rounded-2xl border border-[#d8d7cf] bg-[#fbfaf6] p-6"><h2 className="text-lg font-semibold text-[#173b2b]">{title}</h2><div className="mt-5 flex flex-col gap-5">{children}</div></section> }
function Stat({ label, value, detail }: { label: string; value: React.ReactNode; detail: string }) { return <div className="rounded-xl border border-[#d8d7cf] bg-[#fbfaf6] p-5"><p className="text-sm text-[#66736b]">{label}</p><p className="mt-2 text-3xl font-semibold text-[#173b2b]">{value}</p><p className="mt-2 text-xs text-[#8b968f]">{detail}</p></div> }
function Auth({ mode, onDone }: { mode: 'login' | 'register'; onDone: (user: Me, isNew: boolean) => void }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState(mode === 'login' ? 'amara@example.com' : '')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!email.includes('@') || password.length < 6 || (mode === 'register' && !name.trim())) return setError('Enter a valid email and a password with at least 6 characters.')
    setBusy(true)
    setError('')
    try {
      const body = mode === 'register' ? { name, email, password } : { email, password }
      const result = await post<{ access_token: string; user: Me }>(`/auth/${mode}`, body)
      setToken(result.access_token)
      onDone(result.user, mode === 'register')
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }
  return <div className="grid min-h-screen place-items-center bg-[#f8f7f2] p-6"><form onSubmit={submit} className="w-full max-w-md rounded-2xl border border-[#d8d7cf] bg-[#fbfaf6] p-8"><Logo /><p className="eyebrow mt-10">{mode === 'login' ? 'Welcome back' : 'Start your journey'}</p><h1 className="mt-2 text-3xl font-semibold text-[#173b2b]">{mode === 'login' ? 'Log in to SkillSwap' : 'Create your account'}</h1>{mode === 'register' && <label className="mt-7 block text-sm">Name<input className="field" value={name} onChange={e => setName(e.target.value)} /></label>}<label className="mt-4 block text-sm">Email<input className="field" type="email" value={email} onChange={e => setEmail(e.target.value)} /></label><label className="mt-4 block text-sm">Password<input className="field" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 6 characters" /></label><Notice error={error} /><div className="mt-6"><Button type="submit">{busy ? 'Please wait…' : 'Continue'} <ArrowRight /></Button></div>{mode === 'login' ? <p className="mt-5 text-sm text-[#66736b]">Demo account: amara@example.com / skillswap. New here? <button type="button" className="underline" onClick={() => navigate('/register')}>Create an account</button></p> : <p className="mt-5 text-sm text-[#66736b]">Already registered? <button type="button" className="underline" onClick={() => navigate('/login')}>Log in</button></p>}</form></div>
}

function Shell({ children, route, me, onNavigate, onLogout }: { children: React.ReactNode; route: Route; me: Me; onNavigate: (p: Route) => void; onLogout: () => void }) {
  const items: [Route, string, React.ReactNode][] = [['/dashboard', 'Dashboard', <House key="h" />], ['/discover', 'Discover people', <Compass key="c" />], ['/assessments', 'Assessments', <Award key="a" />], ['/sessions', 'My learning', <BookOpen key="b" />], ['/progress', 'Progress', <Users key="u" />], ['/profile', 'Profile', <Settings key="p" />]]
  return <div className="min-h-screen bg-[#f8f7f2] text-[#26352d]"><header className="flex h-16 items-center justify-between border-b border-[#e4e3db] bg-[#fbfaf6] px-5 md:px-8"><Logo /><div className="flex items-center gap-3"><button aria-label="Messages" onClick={() => onNavigate('/sessions')}><MessageCircle className="size-5 text-[#66736b]" /></button><Avatar initials={me.initials} /><button aria-label="Log out" onClick={onLogout}><LogOut className="size-4 text-[#66736b]" /></button></div></header><div className="mx-auto flex max-w-[1380px]"><aside className="hidden min-h-[calc(100vh-4rem)] w-60 shrink-0 border-r border-[#e4e3db] bg-[#fbfaf6] p-5 md:block"><p className="mb-5 text-[11px] font-semibold uppercase tracking-[.16em] text-[#8b968f]">Workspace</p><nav className="flex flex-col gap-1">{items.map(([path, label, icon]) => <button key={path} onClick={() => onNavigate(path)} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm ${route === path ? 'bg-[#edf3eb] font-medium text-[#173b2b]' : 'text-[#66736b] hover:bg-[#f2f1eb]'}`}>{icon}<span>{label}</span></button>)}</nav></aside><main className="min-w-0 flex-1 p-5 md:p-10">{children}</main></div></div>
}

function Routes({ route, me, refresh, onSaved }: { route: Route; me: Me; refresh: () => void; onSaved: (user: Me) => void }) {
  if (route === '/discover') return <Discover />
  if (route === '/assessments') return <Assessments me={me} refresh={refresh} />
  if (route === '/exchange') return <Exchange />
  if (route === '/sessions') return <Sessions refresh={refresh} />
  if (route === '/progress') return <ProgressPage me={me} />
  if (route === '/profile') return <Profile me={me} onSaved={onSaved} />
  return <Dashboard me={me} />
}

function Dashboard({ me }: { me: Me }) {
  const progress = useLoad(() => api<Progress>('/users/me/progress'), [me.points])
  const exchanges = useLoad(() => api<ExchangeItem[]>('/exchanges'), [])
  return <Page title={`Hello, ${me.name.split(' ')[0]}`} eyebrow="Your dashboard" subtitle="A clear next step makes learning easier."><div className="grid gap-4 md:grid-cols-3"><Stat label="Skill points" value={me.points} detail={progress.data ? `${progress.data.points_to_next_level} points to next level` : 'Loading…'} /><Stat label="Learning goals" value={me.learn.length} detail={me.learn.join(', ') || 'Add a goal in your profile'} /><Stat label="Exchanges" value={exchanges.data?.length ?? 0} detail="Keep the momentum going" /></div><div className="mt-8 grid gap-5 lg:grid-cols-[1.2fr_.8fr]"><Card title="Skills you are working on"><div className="flex flex-wrap gap-2">{me.learn.map(x => <span className="rounded-full bg-[#edf3eb] px-3 py-1.5 text-sm text-[#38704a]" key={x}>{x}</span>)}{!me.learn.length && <p className="text-sm text-[#66736b]">No learning goals yet.</p>}</div><Button variant="outline" onClick={() => navigate('/discover')}>Find a learning partner <ArrowRight /></Button></Card><Card title="Teach what you know"><div className="flex flex-col gap-3">{me.teach.map(skill => <div className="flex items-center justify-between border-b border-[#e4e3db] pb-3 text-sm" key={skill}><span>{skill}</span><span className="text-xs text-[#578064]">{me.verified.includes(skill) ? 'Verified' : 'Unverified'}</span></div>)}{!me.teach.length && <p className="text-sm text-[#66736b]">Add skills you can teach in your profile.</p>}</div><Button onClick={() => navigate('/assessments')}>Verify a skill <Award /></Button></Card></div></Page>
}

function Discover() {
  const [query, setQuery] = useState('')
  const matches = useLoad(() => api<Match[]>(`/matches?min_score=0&q=${encodeURIComponent(query)}`), [query])
  const results = matches.data ?? []
  return <Page eyebrow="Discover" title="People who make learning mutual" subtitle="Search the directory and find a reciprocal goal."><div className="flex items-center gap-2 rounded-lg border border-[#d8d7cf] bg-[#fbfaf6] px-3 py-2.5"><Search className="size-4 text-[#8b968f]" /><input aria-label="Search people" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search people or skills" className="w-full bg-transparent text-sm outline-none" /></div><Notice error={matches.error} /><p className="mt-6 text-sm text-[#66736b]">{matches.loading ? 'Searching…' : `${results.length} people found`}</p><div className="mt-3 flex flex-col gap-3">{results.map(({ person, score, reciprocal, they_teach_you }) => <article className="flex flex-col gap-4 rounded-xl border border-[#d8d7cf] bg-[#fbfaf6] p-5 md:flex-row md:items-center md:justify-between" key={person.id}><div className="flex gap-4"><Avatar initials={person.initials} /><div><h2 className="font-semibold">{person.name}</h2><p className="mt-1 text-sm text-[#66736b]">Teaches {person.teach.join(' · ') || 'nothing yet'}</p><p className="mt-1 text-sm text-[#66736b]">Wants to learn {person.learn.join(' · ') || 'nothing yet'}</p><p className="mt-2 text-xs text-[#578064]">{score}% match{reciprocal ? ' · two-way swap' : ''}{they_teach_you.length ? ` · can teach you ${they_teach_you.join(', ')}` : ''} · {person.rating ? `${person.rating.toFixed(1)} rating` : 'no reviews yet'}</p></div></div><Button onClick={() => navigate(`/exchange?person=${person.id}`)}>Propose exchange <ArrowRight /></Button></article>)}</div></Page>
}

function Assessments({ me, refresh }: { me: Me; refresh: () => void }) {
  const list = useLoad(() => api<AssessmentSummary[]>('/assessments'), [])
  const eligible = (list.data ?? []).filter(a => me.teach.includes(a.skill))
  const [pickedId, setPickedId] = useState<number | null>(null)
  const activeId = pickedId ?? eligible[0]?.id ?? null
  const detail = useLoad(() => (activeId ? api<AssessmentDetail>(`/assessments/${activeId}`) : Promise.resolve(null)), [activeId])
  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState<number[]>([])
  const [result, setResult] = useState<Attempt | null>(null)
  const [error, setError] = useState('')
  const questions = detail.data?.questions ?? []
  const q = questions[index]
  const allAnswered = questions.length > 0 && questions.every((_, i) => typeof answers[i] === 'number')
  function pick(id: number) { setPickedId(id); setIndex(0); setAnswers([]); setResult(null); setError('') }
  async function submit() {
    setError('')
    try {
      const attempt = await post<Attempt>(`/assessments/${activeId}/attempts`, { answers })
      setResult(attempt)
      refresh()
    } catch (err) {
      setError(messageOf(err))
    }
  }
  if (list.loading) return <Page eyebrow="Assessments" title="Show what you know" subtitle="Loading…"><span /></Page>
  if (!eligible.length) return <Page eyebrow="Assessments" title="Show what you know" subtitle="Assessments verify the skills you teach."><Card title="No assessment available yet"><p className="text-sm text-[#66736b]">Assessments exist for {(list.data ?? []).map(a => a.skill).join(', ')}. Add one of these to the skills you can teach in your profile.</p><Button onClick={() => navigate('/profile')}>Edit profile <ArrowRight /></Button></Card></Page>
  if (result) return <Page eyebrow="Assessment complete" title={`${result.score}% score`} subtitle={result.passed ? `${result.skill} qualifies as a verified teaching skill.` : 'You need 75% or above to qualify. You can retry anytime.'}><Card title={result.passed ? (result.newly_verified ? 'Skill verified, +30 points' : 'Skill already verified') : 'Keep practicing'}><p className="text-sm text-[#66736b]">{result.correct_count} of {result.total} answers correct.</p><div className="flex gap-3"><Button onClick={() => pick(activeId!)} variant="outline">Retake</Button><Button onClick={() => navigate('/dashboard')}>Back to dashboard <ArrowRight /></Button></div></Card></Page>
  return <Page eyebrow={`Assessments · ${detail.data?.skill ?? ''}`} title="Show what you know" subtitle={q ? `${index + 1} of ${questions.length}` : 'Loading…'}>{eligible.length > 1 && <div className="mb-4 flex flex-wrap gap-2">{eligible.map(a => <button key={a.id} onClick={() => pick(a.id)} className={`rounded-full border px-4 py-1.5 text-sm ${a.id === activeId ? 'border-[#70a77a] bg-[#edf3eb]' : 'border-[#d8d7cf]'}`}>{a.skill}</button>)}</div>}<Notice error={detail.error} />{q && <><div className="h-1.5 rounded-full bg-[#dfe5dc]"><div className="h-full rounded-full bg-[#4c875d]" style={{ width: `${((index + 1) / questions.length) * 100}%` }} /></div><Card title={q.prompt}><div className="flex flex-col gap-3">{q.options.map((answer, i) => <button key={answer} onClick={() => { const next = [...answers]; next[index] = i; setAnswers(next) }} className={`rounded-xl border p-4 text-left text-sm ${answers[index] === i ? 'border-[#70a77a] bg-[#edf3eb]' : 'border-[#d8d7cf]'}`}><span className="mr-3 text-[#578064]">{String.fromCharCode(65 + i)}</span>{answer}</button>)}</div><Notice error={error} /><div className="mt-8 flex justify-between"><Button variant="text" onClick={() => setIndex(Math.max(0, index - 1))}><ChevronLeft />Previous</Button>{index < questions.length - 1 ? <Button onClick={() => setIndex(index + 1)}>Next <ArrowRight /></Button> : <Button onClick={submit}>{allAnswered ? 'Submit assessment' : 'Answer every question to submit'} <ArrowRight /></Button>}</div></Card></>}</Page>
}

function Exchange() {
  const personId = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').get('person')
  const person = useLoad(() => api<Person>(`/users/${personId}`), [personId])
  const [topic, setTopic] = useState('')
  const [note, setNote] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const p = person.data
  const chosen = topic || p?.teach[0] || ''
  async function send() {
    setError('')
    try {
      await post('/exchanges', { partner_id: p!.id, topic: chosen, note })
      setSent(true)
    } catch (err) {
      setError(messageOf(err))
    }
  }
  if (!p) return <Page eyebrow="Propose an exchange" title="Start an exchange" subtitle={person.loading ? 'Loading…' : 'Person not found.'}><Notice error={person.error} /></Page>
  return <Page eyebrow="Propose an exchange" title={`Start with ${p.name}`} subtitle={`${p.name} can accept or decline your request.`}><Card title="Make the ask clear"><div className="flex items-center gap-4 border-b border-[#e4e3db] pb-5"><Avatar initials={p.initials} /><div><p className="font-semibold">{p.name}</p><p className="text-sm text-[#66736b]">They teach {p.teach.join(' · ') || 'nothing yet'}</p></div></div>{p.teach.length > 0 && <label className="block text-sm">Skill you want to learn<select className="field" value={chosen} onChange={e => setTopic(e.target.value)}>{p.teach.map(skill => <option key={skill}>{skill}</option>)}</select></label>}<label className="block text-sm">Personal note<textarea className="field min-h-28" value={note} onChange={e => setNote(e.target.value)} placeholder="What would you like to learn together?" /></label><Notice error={error} />{sent ? <div className="flex flex-col gap-3"><p className="rounded-lg bg-[#edf3eb] p-3 text-sm text-[#38704a]">Request sent. You can track it in My learning.</p><Button onClick={() => navigate('/sessions')}>Go to My learning <ArrowRight /></Button></div> : <Button onClick={send}>Send exchange request <ArrowRight /></Button>}</Card></Page>
}

function Sessions({ refresh }: { refresh: () => void }) {
  const exchanges = useLoad(() => api<ExchangeItem[]>('/exchanges'), [])
  const [error, setError] = useState('')
  const [reviewing, setReviewing] = useState<number | null>(null)
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')
  const [message, setMessage] = useState('')
  async function act(id: number, action: 'accept' | 'reject' | 'cancel' | 'complete') {
    setError('')
    setMessage('')
    try {
      await post(`/exchanges/${id}/${action}`)
      exchanges.reload()
      refresh()
    } catch (err) {
      setError(messageOf(err))
    }
  }
  async function review(id: number) {
    setError('')
    try {
      await post(`/exchanges/${id}/reviews`, { rating, comment })
      setReviewing(null)
      setComment('')
      setMessage('Review saved, +10 points.')
      refresh()
    } catch (err) {
      setError(messageOf(err))
      if (err instanceof ApiError && err.status === 409) setReviewing(null)
    }
  }
  const list = exchanges.data ?? []
  return <Page eyebrow="My learning" title="Exchanges and sessions" subtitle="Keep every learning commitment in one place."><Notice error={error || exchanges.error} />{message && <p className="mt-3 rounded-lg bg-[#edf3eb] p-3 text-sm text-[#38704a]">{message}</p>}<Card title="Your exchange requests">{list.length ? list.map(x => <div className="border-b border-[#e4e3db] py-4 text-sm" key={x.id}><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-medium">{x.topic}</p><p className="text-[#66736b]">{x.role === 'requester' ? 'You asked' : 'Asked you'} · {x.person.name}{x.note ? ` · “${x.note}”` : ''}</p></div><span className="rounded-full bg-[#edf3eb] px-2.5 py-1 text-xs text-[#38704a]">{x.status}</span></div><div className="mt-3 flex flex-wrap gap-2">{x.status === 'pending' && x.role === 'partner' && <><Button onClick={() => act(x.id, 'accept')}>Accept</Button><Button variant="outline" onClick={() => act(x.id, 'reject')}>Decline</Button></>}{(x.status === 'pending' || x.status === 'accepted') && <Button variant="text" onClick={() => act(x.id, 'cancel')}>Cancel</Button>}{x.status === 'accepted' && <Button onClick={() => act(x.id, 'complete')}>Mark completed</Button>}{x.status === 'completed' && reviewing !== x.id && <Button variant="outline" onClick={() => { setReviewing(x.id); setMessage('') }}>Review {x.person.name.split(' ')[0]}</Button>}</div>{reviewing === x.id && <div className="mt-3 flex flex-col gap-3 rounded-lg bg-[#f2f1eb] p-4"><label>Rating<select className="field" value={rating} onChange={e => setRating(Number(e.target.value))}>{[5, 4, 3, 2, 1].map(n => <option key={n} value={n}>{n} star{n > 1 ? 's' : ''}</option>)}</select></label><label>Comment<textarea className="field" value={comment} onChange={e => setComment(e.target.value)} /></label><div><Button onClick={() => review(x.id)}>Submit review</Button></div></div>}</div>) : <p className="text-sm text-[#66736b]">{exchanges.loading ? 'Loading…' : 'No requests yet. Discover someone to start an exchange.'}</p>}<Button variant="outline" onClick={() => navigate('/discover')}>Discover people <ArrowRight /></Button></Card></Page>
}

function ProgressPage({ me }: { me: Me }) {
  const progress = useLoad(() => api<Progress>('/users/me/progress'), [me.points])
  const p = progress.data
  return <Page eyebrow="Your progress" title="Small steps add up" subtitle="SkillSwap platform achievements are signals of practice, not external qualifications."><Notice error={progress.error} /><div className="grid gap-4 md:grid-cols-3"><Stat label="Skill points" value={p?.points ?? me.points} detail={p ? `${p.points_to_next_level} points to the next level` : 'Earned through eligible activity'} /><Stat label="Current level" value={p?.level ?? '-'} detail={`${p?.verified_skills ?? 0} verified skills`} /><Stat label="Goals active" value={me.learn.length} detail={me.learn.join(', ') || 'None yet'} /></div><Card title="Badges">{p?.achievements.length ? p.achievements.map(a => <div key={a.code} className="text-sm"><p className="font-medium">{a.title}</p><p className="text-[#66736b]">{a.description}</p></div>) : <p className="text-sm text-[#66736b]">No badges yet. Verify a skill or complete an exchange to earn one.</p>}</Card></Page>
}

function SkillPicker({ options, selected, onChange }: { options: string[]; selected: string[]; onChange: (next: string[]) => void }) {
  const [custom, setCustom] = useState('')
  const all = [...options, ...selected.filter(x => !options.includes(x))]
  const toggle = (x: string) => onChange(selected.includes(x) ? selected.filter(y => y !== x) : [...selected, x])
  function add() {
    const name = custom.trim()
    if (name && !selected.includes(name)) onChange([...selected, name])
    setCustom('')
  }
  return <div><div className="grid gap-3 sm:grid-cols-2">{all.map(x => <button type="button" key={x} onClick={() => toggle(x)} className={`rounded-xl border p-4 text-left text-sm ${selected.includes(x) ? 'border-[#70a77a] bg-[#edf3eb]' : 'border-[#d8d7cf]'}`}>{x}{selected.includes(x) && <Check className="float-right size-4" />}</button>)}</div><div className="mt-4 flex gap-2"><input className="field" value={custom} onChange={e => setCustom(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }} placeholder="Add your own skill" /><Button variant="outline" onClick={add}>Add</Button></div></div>
}

function Profile({ me, onSaved }: { me: Me; onSaved: (user: Me) => void }) {
  const [bio, setBio] = useState(me.bio)
  const [teach, setTeach] = useState(me.teach)
  const [learn, setLearn] = useState(me.learn)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  async function save() {
    setError('')
    setSaved(false)
    try {
      await api('/users/me', { method: 'PATCH', body: JSON.stringify({ bio }) })
      onSaved(await api<Me>('/users/me/skills', { method: 'PUT', body: JSON.stringify({ teach, learn }) }))
      setSaved(true)
    } catch (err) {
      setError(messageOf(err))
    }
  }
  return <Page eyebrow="Profile" title={me.name} subtitle={`${me.username} · ${me.email}`}><Card title="About you"><label className="block text-sm">Short bio<textarea className="field min-h-28" value={bio} onChange={e => setBio(e.target.value)} /></label></Card><Card title="Skills you can teach"><SkillPicker options={['UI/UX Design', 'Figma', 'Python', 'Photography']} selected={teach} onChange={setTeach} /></Card><Card title="Skills you want to learn"><SkillPicker options={['Python', 'Public speaking', 'Photography', 'Spanish']} selected={learn} onChange={setLearn} /></Card><Notice error={error} />{saved && <p className="mt-3 rounded-lg bg-[#edf3eb] p-3 text-sm text-[#38704a]">Profile saved.</p>}<div className="mt-6"><Button onClick={save}>Save changes</Button></div></Page>
}

function Onboarding({ me, onSaved }: { me: Me; onSaved: (user: Me) => void }) {
  const [step, setStep] = useState(0)
  const [bio, setBio] = useState(me.bio)
  const [learn, setLearn] = useState(me.learn)
  const [teach, setTeach] = useState(me.teach)
  const [error, setError] = useState('')
  async function finish() {
    setError('')
    try {
      await api('/users/me', { method: 'PATCH', body: JSON.stringify({ bio }) })
      onSaved(await api<Me>('/users/me/skills', { method: 'PUT', body: JSON.stringify({ teach, learn }) }))
    } catch (err) {
      setError(messageOf(err))
    }
  }
  return <div className="min-h-screen bg-[#f8f7f2] p-6"><div className="mx-auto max-w-2xl pt-12"><Logo /><p className="eyebrow mt-16">Step {step + 1} of 3</p><h1 className="mt-2 text-3xl font-semibold text-[#173b2b]">{step === 0 ? 'Let’s start with you' : step === 1 ? 'What do you want to learn?' : 'What can you share?'}</h1><div className="mt-8 rounded-2xl border border-[#d8d7cf] bg-[#fbfaf6] p-6">{step === 0 ? <label className="text-sm">Short bio<textarea className="field min-h-28" value={bio} onChange={e => setBio(e.target.value)} /></label> : step === 1 ? <SkillPicker options={['Python', 'Public speaking', 'Photography', 'Spanish']} selected={learn} onChange={setLearn} /> : <SkillPicker options={['UI/UX Design', 'Figma', 'Product strategy', 'Writing']} selected={teach} onChange={setTeach} />}<Notice error={error} /><div className="mt-8 flex justify-between"><Button variant="text" onClick={() => setStep(Math.max(0, step - 1))}>Back</Button><Button onClick={() => (step < 2 ? setStep(step + 1) : finish())}>{step === 2 ? 'Finish onboarding' : 'Continue'} <ArrowRight /></Button></div></div></div></div>
}

