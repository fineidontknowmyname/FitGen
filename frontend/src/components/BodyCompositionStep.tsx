'use client';

import { useState } from 'react';
import { Camera, Ruler, ClipboardList, SkipForward, Upload, Brain } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select } from '@/components/ui/Select';
import {
    uploadPhotos,
    submitTapeMeasurement,
    submitSelfAssessment,
} from '@/lib/api';
import type { BodyCompositionResult } from '@/lib/api';

type Method = 'select' | 'photo' | 'tape' | 'self';

interface Props {
    heightCm: number;
    gender: 'male' | 'female';
    experienceLevel: string;
    pushupCount?: number;
    squatCount?: number;
    result: BodyCompositionResult | null;
    onResult: (result: BodyCompositionResult | null) => void;
}

const MEASURE_DIAGRAM = (
    <svg viewBox="0 0 120 200" className="w-20 h-32 mx-auto" aria-hidden="true">
        <circle cx="60" cy="20" r="14" fill="none" stroke="#71717a" strokeWidth="2" />
        <path d="M40 40 Q60 34 80 40 L84 150 Q60 160 36 150 Z" fill="none" stroke="#71717a" strokeWidth="2" />
        <line x1="20" y1="52" x2="100" y2="52" stroke="#eab308" strokeWidth="1.5" strokeDasharray="4 3" />
        <text x="60" y="48" textAnchor="middle" fontSize="9" fill="#eab308">Neck</text>
        <line x1="20" y1="100" x2="100" y2="100" stroke="#eab308" strokeWidth="1.5" strokeDasharray="4 3" />
        <text x="60" y="96" textAnchor="middle" fontSize="9" fill="#eab308">Waist</text>
        <line x1="20" y1="140" x2="100" y2="140" stroke="#eab308" strokeWidth="1.5" strokeDasharray="4 3" />
        <text x="60" y="136" textAnchor="middle" fontSize="9" fill="#eab308">Hip</text>
    </svg>
);

function ResultCard({ result }: { result: BodyCompositionResult }) {
    const sourceLabel: Record<string, string> = {
        photo_analysis: 'Photo analysis',
        photo_plus_manual: 'Photo + manual measurement',
        tape_measurement: 'Tape measurement',
        self_assessment: 'Self-assessment',
        unavailable: 'Unavailable',
    };

    return (
        <div className="bg-zinc-900/50 border border-yellow-500/20 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-yellow-500" />
                <h4 className="font-semibold">Body Composition Result</h4>
                {result.source && (
                    <span className="text-xs text-zinc-500 ml-auto">
                        Based on: {sourceLabel[result.source] ?? result.source}
                    </span>
                )}
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/40 p-3 rounded-lg">
                    <span className="text-xs text-zinc-500 block">Est. Body Fat</span>
                    <span className="text-xl font-bold">
                        {result.fat_pct_low != null && result.fat_pct_high != null
                            ? `${result.fat_pct_low}–${result.fat_pct_high}%`
                            : '--'}
                    </span>
                </div>
                <div className="bg-black/40 p-3 rounded-lg">
                    <span className="text-xs text-zinc-500 block">Muscle Level</span>
                    <span className="text-xl font-bold capitalize">
                        {result.muscle_level ? result.muscle_level.replace('_', ' ') : 'Not available'}
                    </span>
                </div>
            </div>
            {result.v_taper_ratio != null && (
                <p className="text-sm"><span className="text-zinc-500">V-Taper: </span>{result.v_taper_ratio}</p>
            )}
            {result.posture_assessment && (
                <p className="text-sm"><span className="text-zinc-500">Posture: </span>{result.posture_assessment}</p>
            )}
            {result.input_completeness === 'partial' && (
                <p className="text-xs text-zinc-500">
                    This result is based on partial input — adding more detail would improve accuracy.
                </p>
            )}
        </div>
    );
}

export default function BodyCompositionStep({
    heightCm, gender, experienceLevel, pushupCount, squatCount, result, onResult,
}: Props) {
    const [method, setMethod] = useState<Method>('select');
    const [error, setError] = useState<string | null>(null);

    const [frontPhoto, setFrontPhoto] = useState<File | null>(null);
    const [sidePhoto, setSidePhoto] = useState<File | null>(null);
    const [backPhoto, setBackPhoto] = useState<File | null>(null);
    const [photoWaistCm, setPhotoWaistCm] = useState('');
    const [photoHipCm, setPhotoHipCm] = useState('');
    const [consentChecked, setConsentChecked] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);
    const [analysisWarning, setAnalysisWarning] = useState<string | null>(null);

    const [neckCm, setNeckCm] = useState('');
    const [tapeWaistCm, setTapeWaistCm] = useState('');
    const [tapeHipCm, setTapeHipCm] = useState('');
    const [tapeSubmitting, setTapeSubmitting] = useState(false);

    const [muscleSep, setMuscleSep] = useState('moderate');
    const [vascularity, setVascularity] = useState('slight');
    const [fatImpression, setFatImpression] = useState('partially_visible');
    const [muscleMass, setMuscleMass] = useState('average');
    const [selfExperience, setSelfExperience] = useState(experienceLevel || 'beginner');
    const [selfSubmitting, setSelfSubmitting] = useState(false);

    const handleAnalyzePhoto = async () => {
        if (!frontPhoto) { setError('Please select a front-view photo.'); return; }
        if (!consentChecked) { setError('Please tick the consent checkbox before uploading.'); return; }
        setAnalyzing(true);
        setError(null);
        setAnalysisWarning(null);
        try {
            const waistCm = photoWaistCm.trim() ? Number(photoWaistCm) : undefined;
            const hipCm = photoHipCm.trim() ? Number(photoHipCm) : undefined;
            const res = await uploadPhotos(
                frontPhoto, sidePhoto, backPhoto, heightCm, gender, true, waistCm, hipCm,
            );
            onResult(res);
            if (!res.pose_detected || res.confidence === 0) {
                setAnalysisWarning(
                    'Could not detect body pose from photo. Estimated values will be used. ' +
                    'Try a clear full-body photo with good lighting and a plain background.'
                );
            }
        } catch (err: unknown) {
            const axiosErr = err as { response?: { status?: number; data?: unknown } };
            if (axiosErr?.response) {
                const status = axiosErr.response.status;
                if (status === 451) setError('Consent required by the server. Please tick the checkbox and try again.');
                else if (status === 400) setError('Invalid image — please use a JPEG/PNG/WebP file, min 200×200px, max 10MB.');
                else setError(`Analysis failed (${status}). Please try again.`);
            } else {
                setError('Could not reach the analysis server — is the API running?');
            }
        } finally { setAnalyzing(false); }
    };

    const handleSubmitTape = async () => {
        if (!neckCm.trim() || !tapeWaistCm.trim() || (gender === 'female' && !tapeHipCm.trim())) {
            setError('Please fill in all required measurements.'); return;
        }
        setTapeSubmitting(true);
        setError(null);
        try {
            const res = await submitTapeMeasurement({
                neck_cm: Number(neckCm),
                waist_cm: Number(tapeWaistCm),
                hip_cm: tapeHipCm.trim() ? Number(tapeHipCm) : undefined,
                height_cm: heightCm,
                gender,
            });
            onResult(res);
        } catch (err: unknown) {
            const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
            setError(axiosErr?.response?.data?.detail ?? 'Could not calculate from these measurements. Please check the values.');
        } finally { setTapeSubmitting(false); }
    };

    const handleSubmitSelf = async () => {
        setSelfSubmitting(true);
        setError(null);
        try {
            const res = await submitSelfAssessment({
                visible_muscle_separation: muscleSep as 'none' | 'slight' | 'moderate' | 'defined' | 'very_defined',
                vascularity: vascularity as 'none' | 'slight' | 'moderate' | 'high',
                body_fat_impression: fatImpression as 'not_visible' | 'partially_visible' | 'visible' | 'very_visible',
                perceived_muscle_mass: muscleMass as 'below_average' | 'average' | 'above_average' | 'well_above_average',
                experience_level: selfExperience as 'beginner' | 'intermediate' | 'advanced',
                pushup_count: pushupCount,
                squat_count: squatCount,
            });
            onResult(res);
        } catch {
            setError('Could not process your self-assessment. Please try again.');
        } finally { setSelfSubmitting(false); }
    };

    if (method === 'select' && !result) {
        return (
            <div className="space-y-6">
                <div>
                    <Label>How would you like to share your body composition?</Label>
                    <p className="text-xs text-zinc-500 mt-1">
                        All three feed the same plan-generation logic — pick whichever is easiest for you.
                    </p>
                </div>
                <div className="grid grid-cols-1 gap-3">
                    <button onClick={() => setMethod('photo')}
                        className="flex items-center gap-4 p-4 rounded-xl bg-zinc-950 border border-white/10 hover:border-yellow-500/40 transition-colors text-left">
                        <Camera className="w-6 h-6 text-yellow-500 shrink-0" />
                        <div>
                            <p className="font-medium">Photo</p>
                            <p className="text-xs text-zinc-500">Upload 1–3 body photos for on-device analysis</p>
                        </div>
                    </button>
                    <button onClick={() => setMethod('tape')}
                        className="flex items-center gap-4 p-4 rounded-xl bg-zinc-950 border border-white/10 hover:border-yellow-500/40 transition-colors text-left">
                        <Ruler className="w-6 h-6 text-yellow-500 shrink-0" />
                        <div>
                            <p className="font-medium">Tape Measurement</p>
                            <p className="text-xs text-zinc-500">Enter neck/waist/hip measurements — no photo needed</p>
                        </div>
                    </button>
                    <button onClick={() => setMethod('self')}
                        className="flex items-center gap-4 p-4 rounded-xl bg-zinc-950 border border-white/10 hover:border-yellow-500/40 transition-colors text-left">
                        <ClipboardList className="w-6 h-6 text-yellow-500 shrink-0" />
                        <div>
                            <p className="font-medium">Quick Self-Assessment</p>
                            <p className="text-xs text-zinc-500">Answer a few questions about how you look and feel</p>
                        </div>
                    </button>
                    <button onClick={() => onResult(null)}
                        className="flex items-center gap-4 p-4 rounded-xl border border-white/5 hover:border-white/20 transition-colors text-left text-zinc-400">
                        <SkipForward className="w-6 h-6 shrink-0" />
                        <div>
                            <p className="font-medium">Skip — use profile data only</p>
                            <p className="text-xs text-zinc-600">You can still generate a full plan without this</p>
                        </div>
                    </button>
                </div>
                <details className="text-xs text-zinc-500">
                    <summary className="cursor-pointer hover:text-zinc-300">How accurate is each method?</summary>
                    <div className="mt-2 space-y-1 pl-1">
                        <p><strong className="text-zinc-400">Tape measurement</strong> uses the US Navy circumference method — the most consistently accurate of the three when measured carefully.</p>
                        <p><strong className="text-zinc-400">Photo analysis</strong> estimates measurements from your photo’s geometry — convenient, somewhat less precise.</p>
                        <p><strong className="text-zinc-400">Self-assessment</strong> is your own read on your physique — useful when you don’t want to measure or photograph, though self-perception varies more than a measured method.</p>
                    </div>
                </details>
            </div>
        );
    }

    if (result) {
        return (
            <div className="space-y-4">
                <ResultCard result={result} />
                <Button variant="ghost" onClick={() => { onResult(null); setMethod('select'); }} className="text-xs">
                    Redo with a different method
                </Button>
            </div>
        );
    }

    if (method === 'photo') {
        return (
            <div className="space-y-6">
                <button onClick={() => setMethod('select')} className="text-xs text-zinc-500 hover:text-yellow-500">&larr; Choose a different method</button>
                {([
                    { file: frontPhoto, setFile: setFrontPhoto, label: 'Front view', required: true },
                    { file: sidePhoto, setFile: setSidePhoto, label: 'Side view', required: false },
                    { file: backPhoto, setFile: setBackPhoto, label: 'Back view', required: false },
                ]).map(({ file, setFile, label, required }, idx) => (
                    <div key={idx} className="space-y-2">
                        <Label>{label}{required && <span className="text-yellow-500 ml-1">*</span>}</Label>
                        <div className="flex items-center gap-3">
                            <input type="file" accept="image/jpeg,image/png,image/webp"
                                id={`photo-input-${idx}`} className="hidden"
                                onChange={e => setFile(e.target.files?.[0] ?? null)} />
                            <label htmlFor={`photo-input-${idx}`}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 cursor-pointer text-sm transition-colors border border-white/5">
                                <Upload className="w-4 h-4" />
                                {file ? file.name : 'Choose file'}
                            </label>
                            {file && <span className="text-xs text-green-400">✓</span>}
                        </div>
                    </div>
                ))}
                <p className="text-xs text-zinc-500">JPG, PNG or WebP · Max 10 MB · Min 200×200 px · Full-body photo recommended</p>

                <div className="space-y-3 pt-2 border-t border-white/5">
                    <div>
                        <Label>Manual Measurements <span className="text-xs text-zinc-500 font-normal">(optional — improves accuracy)</span></Label>
                        <p className="text-xs text-zinc-500 mt-1">Have a tape measure? Add your actual waist/hip circumference and we&apos;ll use it instead of estimating it from the photo.</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label className="text-xs">Waist (cm)</Label>
                            <Input type="number" placeholder="e.g. 82" min={30} max={250} value={photoWaistCm} onChange={e => setPhotoWaistCm(e.target.value)} />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-xs">Hip (cm)</Label>
                            <Input type="number" placeholder="e.g. 98" min={30} max={250} value={photoHipCm} onChange={e => setPhotoHipCm(e.target.value)} />
                        </div>
                    </div>
                </div>

                <label className="flex items-start gap-3 p-3 rounded-lg bg-zinc-950 border border-white/10 cursor-pointer">
                    <input type="checkbox" checked={consentChecked} onChange={e => setConsentChecked(e.target.checked)}
                        className="accent-yellow-500 mt-0.5" />
                    <span className="text-xs text-zinc-400">
                        I consent to my photo(s) being analysed on-device for body composition estimation.
                        Photos are processed locally and never shared.
                    </span>
                </label>

                <Button variant="secondary" onClick={handleAnalyzePhoto}
                    disabled={analyzing || !frontPhoto || !consentChecked} className="w-full">
                    {analyzing ? 'Analysing…' : 'Analyse Photos'}
                </Button>
                {error && <p className="text-red-400 text-xs">{error}</p>}
                {analysisWarning && (
                    <div className="flex gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-sm text-yellow-400">
                        <span>⚠️</span><p>{analysisWarning}</p>
                    </div>
                )}
            </div>
        );
    }

    if (method === 'tape') {
        return (
            <div className="space-y-6">
                <button onClick={() => setMethod('select')} className="text-xs text-zinc-500 hover:text-yellow-500">&larr; Choose a different method</button>
                {MEASURE_DIAGRAM}
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label>Neck (cm)</Label>
                        <Input type="number" placeholder="e.g. 38" value={neckCm} onChange={e => setNeckCm(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                        <Label>Waist (cm)</Label>
                        <Input type="number" placeholder="e.g. 85" value={tapeWaistCm} onChange={e => setTapeWaistCm(e.target.value)} />
                    </div>
                </div>
                {gender === 'female' && (
                    <div className="space-y-2">
                        <Label>Hip (cm) <span className="text-yellow-500">*</span></Label>
                        <Input type="number" placeholder="e.g. 98" value={tapeHipCm} onChange={e => setTapeHipCm(e.target.value)} />
                    </div>
                )}
                <p className="text-xs text-zinc-500">
                    Measure directly against skin, relaxed (not sucked in), tape parallel to the floor. Height ({heightCm} cm) is taken from your profile.
                </p>
                <Button variant="secondary" onClick={handleSubmitTape} disabled={tapeSubmitting} className="w-full">
                    {tapeSubmitting ? 'Calculating…' : 'Calculate'}
                </Button>
                {error && <p className="text-red-400 text-xs">{error}</p>}
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <button onClick={() => setMethod('select')} className="text-xs text-zinc-500 hover:text-yellow-500">&larr; Choose a different method</button>

            <div className="space-y-2">
                <Label>Visible muscle separation</Label>
                <Select value={muscleSep} onChange={e => setMuscleSep(e.target.value)}>
                    <option value="none">None</option>
                    <option value="slight">Slight</option>
                    <option value="moderate">Moderate</option>
                    <option value="defined">Defined</option>
                    <option value="very_defined">Very defined</option>
                </Select>
            </div>
            <div className="space-y-2">
                <Label>Vascularity</Label>
                <Select value={vascularity} onChange={e => setVascularity(e.target.value)}>
                    <option value="none">None</option>
                    <option value="slight">Slight</option>
                    <option value="moderate">Moderate</option>
                    <option value="high">High</option>
                </Select>
            </div>
            <div className="space-y-2">
                <Label>How visible are your abs?</Label>
                <Select value={fatImpression} onChange={e => setFatImpression(e.target.value)}>
                    <option value="not_visible">Not visible</option>
                    <option value="partially_visible">Partially visible</option>
                    <option value="visible">Visible</option>
                    <option value="very_visible">Very visible</option>
                </Select>
            </div>
            <div className="space-y-2">
                <Label>Perceived muscle mass (vs. peers)</Label>
                <Select value={muscleMass} onChange={e => setMuscleMass(e.target.value)}>
                    <option value="below_average">Below average</option>
                    <option value="average">Average</option>
                    <option value="above_average">Above average</option>
                    <option value="well_above_average">Well above average</option>
                </Select>
            </div>
            <div className="space-y-2">
                <Label>Training experience</Label>
                <Select value={selfExperience} onChange={e => setSelfExperience(e.target.value)}>
                    <option value="beginner">Beginner (0–1 years)</option>
                    <option value="intermediate">Intermediate (1–3 years)</option>
                    <option value="advanced">Advanced (3+ years)</option>
                </Select>
            </div>
            <p className="text-xs text-zinc-500">
                Self-reported results are inherently less precise than a measured or photo-based estimate —
                we&apos;ll weigh this accordingly when building your plan.
            </p>
            <Button variant="secondary" onClick={handleSubmitSelf} disabled={selfSubmitting} className="w-full">
                {selfSubmitting ? 'Submitting…' : 'Submit Self-Assessment'}
            </Button>
            {error && <p className="text-red-400 text-xs">{error}</p>}
        </div>
    );
}
