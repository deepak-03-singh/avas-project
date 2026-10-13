import { useState } from 'react'
import { FileText, UploadCloud, CheckCircle2, CircleAlert, Search, LoaderCircle, Sparkles, ShieldCheck } from 'lucide-react'

const API = `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api`
type Section = { name: string; status: 'found' | 'not_detected'; evidence: string | null }
type Review = { document_type: string; page_count: number; characters_extracted: number; evidence_coverage_percent: number; coverage_note: string; sections: Section[]; detected_sections: string[]; sections_to_review: string[]; founder_questions: string[]; warnings: string[]; text_preview: string }
type Claim = { claim: string; reason: string; evidence_quote: string }
type ExtractedField = { key: string; label: string; kind: string; value: string | null; evidence_quote: string; confidence: string; status: string }
type Extraction = { fields: ExtractedField[]; method: string; model: string; page_count: number; text_characters_reviewed: number; text_was_truncated: boolean; notice: string }
type AIReview = { provider: string; method: string; model: string; executive_summary: string; strengths: string[]; concerns: string[]; financial_review: string[]; claims_to_verify: Claim[]; founder_questions: string[]; diligence_checklist: string[]; limitations: string[]; disclaimer: string; text_characters_reviewed: number; text_was_truncated: boolean }

type ImportField = { key: string; label: string; value: string | null; evidence_quote?: string; confidence?: string; status?: string }
type Profile = Record<string, string | number | boolean>
export default function PitchDeck({ token, currentForm, onImport }: { token: string; currentForm: Profile; onImport: (fields: ImportField[]) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [review, setReview] = useState<Review | null>(null)
  const [aiReview, setAiReview] = useState<AIReview | null>(null)
  const [extraction, setExtraction] = useState<Extraction | null>(null)
  const [extractBusy, setExtractBusy] = useState(false)
  const [extractError, setExtractError] = useState('')
  const [busy, setBusy] = useState(false)
  const [aiBusy, setAiBusy] = useState(false)
  const [error, setError] = useState('')
  const [aiError, setAiError] = useState('')
  const [notice, setNotice] = useState('')

  async function uploadTo(endpoint: string) {
    if (!file) throw new Error('Choose a PDF pitch deck first.')
    const data = new FormData()
    data.append('file', file)
    const response = await fetch(`${API}/pitch-deck/${endpoint}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: data })
    let body: any = {}
    try { body = await response.json() } catch { /* response may not be JSON */ }
    if (!response.ok) throw new Error(body.detail || 'Could not analyze this PDF.')
    return body
  }

  async function analyze() {
    setBusy(true); setError(''); setNotice('')
    try {
      setReview(await uploadTo('analyze'))
      setNotice('Checklist review completed. The PDF was processed in memory and not saved by this endpoint.')
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not connect to the backend.') }
    finally { setBusy(false) }
  }

  async function extractData() {
    setExtractBusy(true); setExtractError('')
    try { setExtraction(await uploadTo('extract-data')) }
    catch (e) { setExtractError(e instanceof Error ? e.message : 'Could not extract structured data.') }
    finally { setExtractBusy(false) }
  }

  function updateExtractedField(key: string, value: string) {
    setExtraction(prev => prev ? { ...prev, fields: prev.fields.map(field => field.key === key ? { ...field, value, status: value.trim() ? 'edited_or_extracted' : 'not_found' } : field) } : prev)
  }

  function numericValue(value: unknown, kind: 'plain' | 'millions' = 'plain'): number | null {
    if (value === null || value === undefined || String(value).trim() === '') return null
    const raw = String(value).replace(/,/g, '').trim()
    const match = raw.match(/-?\d+(?:\.\d+)?/)
    if (!match) return null
    let number = Number(match[0])
    const suffix = raw.slice(match.index! + match[0].length).trim().match(/^([kmb])/i)?.[1]?.toLowerCase()
    if (suffix === 'k') number *= 1_000
    if (suffix === 'm') number *= 1_000_000
    if (suffix === 'b') number *= 1_000_000_000
    if (kind === 'millions') number /= 1_000_000
    return Number.isFinite(number) ? number : null
  }

  const comparisons = extraction ? ([
    { key: 'startup_name', label: 'Startup name', extractedKey: 'startup_name', numeric: false },
    { key: 'industry', label: 'Industry', extractedKey: 'industry', numeric: false },
    { key: 'monthly_revenue', label: 'Monthly revenue', extractedKey: 'monthly_revenue', numeric: true },
    { key: 'monthly_burn', label: 'Monthly burn', extractedKey: 'monthly_burn', numeric: true },
    { key: 'financial_runway_months', label: 'Runway (months)', extractedKey: 'runway_months', numeric: true },
    { key: 'funding_needed', label: 'Funding needed', extractedKey: 'funding_ask', numeric: true },
    { key: 'target_market_size_millions', label: 'Market size (millions)', extractedKey: 'market_size', numeric: true, millions: true },
    { key: 'customer_validation_count', label: 'Paying customers / validation count', extractedKey: 'paying_customers', numeric: true },
  ] as { key: string; label: string; extractedKey: string; numeric: boolean; millions?: boolean }[]).map(item => {
    const extracted = extraction.fields.find(field => field.key === item.extractedKey)?.value ?? null
    const entered = currentForm[item.key]
    const left = item.numeric ? numericValue(entered, item.millions ? 'millions' : 'plain') : String(entered ?? '').trim().toLowerCase()
    const right = item.numeric ? numericValue(extracted, item.millions ? 'millions' : 'plain') : String(extracted ?? '').trim().toLowerCase()
    const bothPresent = extracted !== null && String(extracted).trim() !== '' && entered !== undefined && String(entered).trim() !== ''
    const match = bothPresent && left !== null && right !== null && (item.numeric ? Math.abs(Number(left) - Number(right)) <= Math.max(1, Math.abs(Number(left)) * 0.05) : left === right)
    return { ...item, extracted, entered, bothPresent, match }
  }) : []

  function exportExtractionCsv() {
    if (!extraction) return
    const escape = (value: unknown) => `"${String(value ?? '').replace(/"/g, '""')}"`
    const rows = [['Field', 'Value (editable)', 'Evidence quote', 'Confidence', 'Status'], ...extraction.fields.map(f => [f.label, f.value ?? '', f.evidence_quote, f.confidence, f.status])]
    const csv = rows.map(row => row.map(escape).join(',')).join('\r\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
    const link = document.createElement('a'); link.href = url; link.download = 'avas-extracted-startup-data.csv'; link.click(); URL.revokeObjectURL(url)
  }

  async function analyzeWithAI() {
    setAiBusy(true); setAiError('')
    try { setAiReview(await uploadTo('ai-review')) }
    catch (e) { setAiError(e instanceof Error ? e.message : 'Could not connect to the AI provider.') }
    finally { setAiBusy(false) }
  }

  function chooseFile(next: File | null) {
    setFile(next); setReview(null); setAiReview(null); setExtraction(null); setError(''); setAiError(''); setExtractError(''); setNotice('')
  }

  return <div className="pitch-page">
    <section className="section-heading"><div><div className="section-kicker">03 / DOCUMENT INTELLIGENCE</div><h2>Pitch deck review</h2><p>Review common sections or run an optional AI-assisted, evidence-focused review.</p></div><div className="pill"><FileText size={14} /> PDF analysis</div></section>
    <section className="form-card pitch-upload-card">
      <div className="form-section-title"><div className="mini-icon"><UploadCloud size={18} /></div><div><b>Upload a pitch deck</b><small>PDF only · Up to 10 MB · Maximum 50 pages</small></div></div>
      <label className="upload-drop"><UploadCloud size={30} /><b>{file ? file.name : 'Choose your startup pitch deck'}</b><span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Text-based PDF works best; scanned PDFs are not supported yet.'}</span><input type="file" accept="application/pdf,.pdf" onChange={e => chooseFile(e.target.files?.[0] || null)} /></label>
      {error && <div className="error-msg">{error}</div>}{notice && <div className="notice-msg">{notice}</div>}
      <div className="form-footer"><span><CircleAlert size={15} /> PDF is not saved; AI review and data extraction send extracted text to your configured provider.</span><div className="pitch-actions"><button onClick={analyze} disabled={busy || aiBusy || extractBusy || !file}>{busy ? <><LoaderCircle size={16} className="spin" /> Analyzing…</> : <>Checklist review <Search size={16} /></>}</button><button className="ai-review-button" onClick={analyzeWithAI} disabled={busy || aiBusy || extractBusy || !file}>{aiBusy ? <><LoaderCircle size={16} className="spin" /> AI reviewing…</> : <>AI review <Sparkles size={16} /></>}</button><button className="extract-data-button" onClick={extractData} disabled={busy || aiBusy || extractBusy || !file}>{extractBusy ? <><LoaderCircle size={16} className="spin" /> Extracting…</> : <>Extract data <FileText size={16} /></>}</button></div></div>
      {aiError && <div className="error-msg ai-error"><b>AI review:</b> {aiError}{aiError.toLowerCase().includes('llm_api_key') && <p>To enable it, add your provider key to <code>backend/.env</code>, set <code>LLM_MODEL</code> if needed, then restart the backend. Never put the key in frontend code or share it publicly.</p>}</div>}
    </section>

    {extractError && <div className="error-msg ai-error"><b>Data extraction:</b> {extractError}<p>Requires the optional LLM_API_KEY setting in backend/.env. The standard checklist remains available without it.</p></div>}

    {extraction && <section className="result-card extraction-results">
      <div className="card-heading"><div><div className="section-kicker">PHASE 6 / STRUCTURED DATA EXTRACTION</div><h3>Extracted startup data</h3><p>{extraction.fields.filter(f => f.value !== null && String(f.value).trim()).length} of {extraction.fields.length} fields populated · {extraction.text_characters_reviewed.toLocaleString()} text characters reviewed{extraction.text_was_truncated ? ' (text truncated)' : ''}</p></div><FileText size={20} /></div>
      <div className="extraction-notice"><ShieldCheck size={16} /> {extraction.notice} Quotes are checked against extracted PDF text, but the underlying claim is not independently verified.</div>
      <div className="extraction-grid">{extraction.fields.map(field => <label className="extraction-field" key={field.key}><span>{field.label}</span><input value={field.value ?? ''} placeholder="Not found — enter manually" onChange={e => updateExtractedField(field.key, e.target.value)} /><small>{field.status === 'not_found' ? 'Not found in text · manual entry available' : `Confidence: ${field.confidence}`}</small>{field.evidence_quote && <blockquote>“{field.evidence_quote}”</blockquote>}</label>)}</div>
      <div className="form-footer extraction-footer"><span>Review and correct fields before using them in an assessment.</span><div className="pitch-actions"><button className="secondary-button" onClick={() => onImport(extraction.fields)}>Use in assessment form</button><button onClick={exportExtractionCsv}>Export editable data as CSV</button></div></div>
      <div className="result-card integration-card"><div className="card-heading"><div><div className="section-kicker">PHASE 7 / ASSESSMENT INTEGRATION</div><h3>Compare against assessment form</h3><p>Compares extractable values with the current form. A missing value is not treated as a match.</p></div><Search size={18}/></div><div className="comparison-table-wrap"><table className="comparison-table"><thead><tr><th>Field</th><th>Current assessment</th><th>Pitch deck</th><th>Comparison</th></tr></thead><tbody>{comparisons.map(row=><tr key={row.key}><td>{row.label}</td><td>{String(row.entered ?? '—')}</td><td>{row.extracted ?? 'Not found'}</td><td>{!row.bothPresent ? <span className="comparison-status review">Review / missing</span> : row.match ? <span className="comparison-status match">Consistent</span> : <span className="comparison-status mismatch">Difference</span>}</td></tr>)}</tbody></table></div><p className="comparison-note">Numeric comparison allows a 5% tolerance for ordinary fields. Market-size amounts are normalized to millions when a clear number and unit are present. Confirm units and currency manually.</p><button className="secondary-button" onClick={() => { const rows = [['Field','Current assessment','Pitch deck extraction','Status'], ...comparisons.map(row => [row.label, row.entered ?? '', row.extracted ?? '', !row.bothPresent ? 'Review / missing' : row.match ? 'Consistent' : 'Difference'])]; const csv = rows.map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\r\n'); const url = URL.createObjectURL(new Blob([csv], {type:'text/csv;charset=utf-8;'})); const link = document.createElement('a'); link.href=url; link.download='avas-discrepancy-report.csv'; link.click(); URL.revokeObjectURL(url) }}>Export discrepancy report</button></div>
    </section>}

    {aiReview && <section className="ai-review-results">
      <div className="result-card ai-summary-card"><div className="card-heading"><div><div className="section-kicker">PHASE 5 / AI-ASSISTED REVIEW</div><h3>Executive summary</h3><p>Model: {aiReview.model} · {aiReview.text_characters_reviewed.toLocaleString()} text characters reviewed{aiReview.text_was_truncated ? ' (text was truncated)' : ''}</p></div><Sparkles size={20} /></div><p className="ai-summary-text">{aiReview.executive_summary}</p><div className="ai-disclaimer"><ShieldCheck size={16} /> {aiReview.disclaimer}</div></div>
      <div className="ai-columns">
        <div className="result-card ai-list-card"><div className="card-heading"><div><h3>Potential strengths</h3><p>Signals described in the deck; verify the evidence.</p></div><CheckCircle2 size={18} /></div>{aiReview.strengths.length ? <ul>{aiReview.strengths.map((x, i) => <li key={i}>{x}</li>)}</ul> : <p className="ai-empty">No specific strengths were returned.</p>}</div>
        <div className="result-card ai-list-card"><div className="card-heading"><div><h3>Concerns & gaps</h3><p>Issues to investigate, not definitive findings.</p></div><CircleAlert size={18} /></div>{aiReview.concerns.length ? <ul>{aiReview.concerns.map((x, i) => <li key={i}>{x}</li>)}</ul> : <p className="ai-empty">No specific concerns were returned.</p>}</div>
      </div>
      <div className="result-card ai-list-card"><div className="card-heading"><div><h3>Financial review</h3><p>Financial assumptions mentioned or missing in the document.</p></div><FileText size={18} /></div><ul>{(aiReview.financial_review.length ? aiReview.financial_review : ['No detailed financial observations were returned.']).map((x, i) => <li key={i}>{x}</li>)}</ul></div>
      <div className="result-card ai-claims-card"><div className="card-heading"><div><h3>Claims to verify</h3><p>Ask for primary sources before relying on these statements.</p></div><Search size={18} /></div>{aiReview.claims_to_verify.length ? <div className="ai-claim-list">{aiReview.claims_to_verify.map((c, i) => <article key={i} className="ai-claim"><b>{c.claim}</b><p>{c.reason}</p>{c.evidence_quote && <blockquote>“{c.evidence_quote}”</blockquote>}</article>)}</div> : <p className="ai-empty">No specific claims were returned. This does not mean the deck's claims are verified.</p>}</div>
      <div className="ai-columns">
        <div className="result-card ai-list-card"><div className="card-heading"><div><h3>Founder questions</h3><p>Questions to use in a discussion.</p></div><Search size={18} /></div><ol>{aiReview.founder_questions.map((x, i) => <li key={i}>{x}</li>)}</ol></div>
        <div className="result-card ai-list-card"><div className="card-heading"><div><h3>Due-diligence checklist</h3><p>Suggested follow-up evidence to collect.</p></div><CheckCircle2 size={18} /></div><ul>{aiReview.diligence_checklist.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
      </div>
      <div className="result-card pitch-warnings"><div className="card-heading"><div><h3>Limitations & privacy</h3><p>AI can misunderstand or misstate document details.</p></div><CircleAlert size={18} /></div><ul>{aiReview.limitations.map((x, i) => <li key={i}>{x}</li>)}</ul><p className="ai-privacy-note">Only extracted text (up to 28,000 characters) is sent to the configured AI provider. Review that provider's privacy and retention terms before using confidential pitch decks. The AVAS endpoint does not save the uploaded PDF.</p></div>
    </section>}

    {review && <section className="pitch-results"><div className="metrics-grid"><div className="metric-card score-card"><div className="metric-label">TOPIC COVERAGE <CheckCircle2 size={17} /></div><div className="score-line"><strong>{review.evidence_coverage_percent}</strong><span>/ 100</span></div><div className="progress"><i style={{ width: `${review.evidence_coverage_percent}%` }} /></div><p>Common topics detected</p></div><div className="metric-card"><div className="metric-label">PAGES <FileText size={17} /></div><div className="model-word">{review.page_count}</div><p>PDF pages processed</p><div className="metric-bottom">{review.characters_extracted.toLocaleString()} characters extracted</div></div><div className="metric-card"><div className="metric-label">DETECTED <CheckCircle2 size={17} /></div><div className="model-word">{review.detected_sections.length}<small> / {review.sections.length}</small></div><p>Pitch-deck topic groups</p></div><div className="metric-card"><div className="metric-label">TO REVIEW <CircleAlert size={17} /></div><div className="model-word">{review.sections_to_review.length}</div><p>Topics not detected</p></div></div>
      <div className="result-card pitch-section-card"><div className="card-heading"><div><h3>Section checklist</h3><p>{review.coverage_note}</p></div><FileText size={18} /></div><div className="pitch-section-list">{review.sections.map(s => <div className="pitch-section-row" key={s.name}><div className={s.status === 'found' ? 'section-status found' : 'section-status missing'}>{s.status === 'found' ? <CheckCircle2 size={17} /> : <CircleAlert size={17} />}</div><div className="pitch-section-content"><b>{s.name}</b>{s.evidence && <p>{s.evidence}</p>}{s.status === 'not_detected' && <small>Not detected by keyword checks; manually confirm in the original deck.</small>}</div><span className={s.status === 'found' ? 'status-label found' : 'status-label missing'}>{s.status === 'found' ? 'Detected' : 'Review'}</span></div>)}</div></div>
      {review.founder_questions.length > 0 && <div className="result-card pitch-questions"><div className="card-heading"><div><h3>Questions to ask the founder</h3><p>Questions generated from topics not detected in the text.</p></div><Search size={18} /></div><ol>{review.founder_questions.map((q, i) => <li key={i}>{q}</li>)}</ol></div>}
      <div className="result-card pitch-warnings"><div className="card-heading"><div><h3>Method and limitations</h3><p>This is a document checklist, not an automated investment decision.</p></div><CircleAlert size={18} /></div><ul>{review.warnings.map(w => <li key={w}>{w}</li>)}</ul><details><summary>Text preview (first 1,200 characters)</summary><pre>{review.text_preview}</pre></details></div>
    </section>}
  </div>
}
