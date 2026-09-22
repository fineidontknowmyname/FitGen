'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select } from '@/components/ui/Select';
import Header from '@/components/layout/Header';
import { ArrowLeft, ArrowRight, Plus, X } from 'lucide-react';
import BodyCompositionStep from '@/components/BodyCompositionStep';
import type { BodyCompositionResult } from '@/lib/api';

const STEPS = [
    { id: 'biometrics', title: 'Biometrics', description: "Let's get to know your physical stats." },
    { id: 'activity', title: 'Activity', description: 'Tell us how active you already are.' },
    { id: 'metrics', title: 'Baseline', description: 'What can you do right now?' },
    { id: 'goals', title: 'Goals', description: 'What are you aiming for?' },
    { id: 'equipment', title: 'Equipment & Injuries', description: 'What do you have access to, and anything we should avoid?' },
    { id: 'videos', title: 'Videos', description: 'Add YouTube videos to build your plan from.' },
    { id: 'photos', title: 'Analysis', description: 'Upload photos for AI body composition analysis.' },
];

const EQUIPMENT_OPTIONS = [
    { value: 'bodyweight', label: 'Bodyweight only' },
    { value: 'dumbbell', label: 'Dumbbells' },
    { value: 'barbell', label: 'Barbell' },
    { value: 'resistance_band', label: 'Resistance bands' },
    { value: 'machine', label: 'Gym machines' },
] as const;

const INJURY_OPTIONS = [
    { value: 'shoulder', label: 'Shoulder' },
    { value: 'knee', label: 'Knee' },
    { value: 'back', label: 'Back' },
    { value: 'wrist', label: 'Wrist' },
    { value: 'ankle', label: 'Ankle' },
] as const;

interface FormData {
    age: string; weight: string; height: string; gender: 'male' | 'female';
    activityHoursPerWeek: number; activityLevel: string;
    pushups: string; situps: string; squats: string;
    goal: string; experience: string;
    youtubeUrls: string[];
    equipment: string[]; injuries: string[];
}

const DEFAULT: FormData = {
    age: '', weight: '', height: '', gender: 'male',
    activityHoursPerWeek: 3, activityLevel: 'moderately_active',
    pushups: '', situps: '', squats: '',
    goal: 'muscle_gain', experience: 'beginner',
    youtubeUrls: [''],
    equipment: [], injuries: [],
};

export default function OnboardingPage() {
    const [step, setStep] = useState(0);
    const [form, setForm] = useState<FormData>(DEFAULT);
    const [result, setResult] = useState<BodyCompositionResult | null>(null);
    const [ageError, setAgeError] = useState('');

    const set = (f: keyof FormData, v: unknown) => setForm(p => ({ ...p, [f]: v }));

    const toggleEquipment = (value: string) => setForm(p => ({
        ...p,
        equipment: p.equipment.includes(value)
            ? p.equipment.filter(e => e !== value)
            : [...p.equipment, value],
    }));

    const toggleInjury = (value: string) => setForm(p => ({
        ...p,
        injuries: p.injuries.includes(value)
            ? p.injuries.filter(i => i !== value)
            : [...p.injuries, value],
    }));

    const addUrl = () => set('youtubeUrls', [...form.youtubeUrls, '']);
    const removeUrl = (i: number) => set('youtubeUrls', form.youtubeUrls.filter((_, x) => x !== i));
    const updateUrl = (i: number, v: string) => set('youtubeUrls', form.youtubeUrls.map((u, x) => x === i ? v : u));

    const handleNext = () => {
        if (step === 0) {
            const age = Number(form.age);
            if (!form.age || isNaN(age) || age < 15 || age > 60) {
                setAgeError('Age must be between 15 and 60.'); return;
            }
            setAgeError('');
        }
        if (step < STEPS.length - 1) { setStep(p => p + 1); }
        else {
            const existing = (() => {
                try { return JSON.parse(localStorage.getItem('fitgen_user') || '{}'); }
                catch { return {}; }
            })();

            const userData = {
                ...existing,
                age: Number(form.age) || existing.age,
                gender: form.gender,
                weight_kg: Number(form.weight) || existing.weight_kg,
                height_cm: Number(form.height) || existing.height_cm,
                fitness_goal: form.goal,
                experience_level: form.experience,
                pushups_max: Number(form.pushups) || 0,
                squats_max: Number(form.squats) || 0,
                physical_activity_hours_per_day: (form.activityHoursPerWeek ?? 7) / 7,
                equipment_available: form.equipment ?? [],
                injuries: form.injuries ?? [],
                ...(result ? {
                    body_fat_pct: result.fat_pct_low != null && result.fat_pct_high != null
                        ? `${result.fat_pct_low}-${result.fat_pct_high}`
                        : existing.body_fat_pct,
                    muscle_level: result.muscle_level ?? existing.muscle_level,
                    v_taper: result.v_taper_ratio ?? existing.v_taper,
                    body_composition_source: result.source ?? existing.body_composition_source,
                    body_composition: result,
                } : {}),
            };

            localStorage.setItem('fitgen_user', JSON.stringify(userData));
            localStorage.setItem('fitgen_onboarded', 'true');
            window.location.href = '/dashboard';
        }
    };

    const hoursLabel = (h: number) =>
        h === 0 ? 'Sedentary' : h <= 3 ? 'Lightly active' : h <= 6 ? 'Moderately active' : h <= 10 ? 'Very active' : 'Extremely active';

    return (
        <div className="min-h-screen bg-black text-white flex flex-col">
            <Header />
            <main className="flex-1 max-w-2xl mx-auto w-full px-6 py-20">
                <div className="mb-12">
                    <span className="text-yellow-500 font-medium text-sm block mb-1">Step {step + 1} of {STEPS.length}</span>
                    <h1 className="font-heading text-2xl font-semibold">{STEPS[step].title}</h1>
                    <p className="text-zinc-400 mt-1">{STEPS[step].description}</p>
                    <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden mt-4">
                        <motion.div className="h-full bg-yellow-500"
                            animate={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
                            transition={{ duration: 0.3 }} />
                    </div>
                </div>

                <div className="bg-zinc-900/30 border border-white/5 rounded-2xl p-8">
                    <AnimatePresence mode="wait">
                        <motion.div key={step}
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>

                            {step === 0 && (
                                <div className="space-y-6">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Age <span className="text-xs text-zinc-500">(15–60)</span></Label>
                                            <Input type="number" placeholder="25" min={15} max={60}
                                                value={form.age} onChange={e => { set('age', e.target.value); setAgeError(''); }} />
                                            {ageError && <p className="text-red-400 text-xs">{ageError}</p>}
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Gender</Label>
                                            <Select value={form.gender} onChange={e => set('gender', e.target.value as 'male' | 'female')}>
                                                <option value="male">Male</option>
                                                <option value="female">Female</option>
                                            </Select>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Weight (kg)</Label>
                                            <Input type="number" placeholder="70" value={form.weight} onChange={e => set('weight', e.target.value)} />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Height (cm)</Label>
                                            <Input type="number" placeholder="175" value={form.height} onChange={e => set('height', e.target.value)} />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {step === 1 && (
                                <div className="space-y-6">
                                    <div className="space-y-3">
                                        <Label>Weekly training hours: <span className="text-yellow-500 font-semibold">{form.activityHoursPerWeek} hr{form.activityHoursPerWeek !== 1 ? 's' : ''}</span></Label>
                                        <input type="range" min={0} max={20} step={1}
                                            value={form.activityHoursPerWeek}
                                            onChange={e => set('activityHoursPerWeek', Number(e.target.value))}
                                            className="w-full accent-yellow-500 cursor-pointer" />
                                        <div className="flex justify-between text-xs text-zinc-500"><span>0</span><span>10</span><span>20</span></div>
                                        <p className="text-sm text-zinc-300 font-medium">{hoursLabel(form.activityHoursPerWeek)}</p>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Activity Level</Label>
                                        <Select value={form.activityLevel} onChange={e => set('activityLevel', e.target.value)}>
                                            <option value="sedentary">Sedentary</option>
                                            <option value="lightly_active">Light (1–3 days/week)</option>
                                            <option value="moderately_active">Moderate (3–5 days/week)</option>
                                            <option value="very_active">Active (6–7 days/week)</option>
                                            <option value="extra_active">Extra active</option>
                                        </Select>
                                    </div>
                                </div>
                            )}

                            {step === 2 && (
                                <div className="space-y-6">
                                    <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                                        <p className="text-sm text-yellow-500">Be honest — FitGen needs accurate data to build a safe plan.</p>
                                    </div>
                                    {(['pushups', 'squats', 'situps'] as const).map(k => (
                                        <div key={k} className="space-y-2">
                                            <Label>Max {k.charAt(0).toUpperCase() + k.slice(1)} (in one go)</Label>
                                            <Input type="number" placeholder="20" value={form[k]} onChange={e => set(k, e.target.value)} />
                                        </div>
                                    ))}
                                </div>
                            )}

                            {step === 3 && (
                                <div className="space-y-6">
                                    <div className="space-y-2">
                                        <Label>Primary Goal</Label>
                                        <Select value={form.goal} onChange={e => set('goal', e.target.value)}>
                                            <option value="muscle_gain">Hypertrophy (Build Muscle)</option>
                                            <option value="strength_gain">Strength (Get Stronger)</option>
                                            <option value="endurance_gain">Endurance</option>
                                            <option value="weight_loss">Weight Loss</option>
                                            <option value="flexibility_gain">Flexibility</option>
                                            <option value="general_fitness">General Fitness</option>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Experience Level</Label>
                                        <Select value={form.experience} onChange={e => set('experience', e.target.value)}>
                                            <option value="beginner">Beginner (0–1 years)</option>
                                            <option value="intermediate">Intermediate (1–3 years)</option>
                                            <option value="advanced">Advanced (3+ years)</option>
                                        </Select>
                                    </div>
                                </div>
                            )}

                            {step === 4 && (
                                <div className="space-y-8">
                                    <div className="space-y-3">
                                        <Label>Available Equipment</Label>
                                        <div className="grid grid-cols-2 gap-2">
                                            {EQUIPMENT_OPTIONS.map(opt => (
                                                <label key={opt.value}
                                                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-zinc-950 border border-white/10 text-sm cursor-pointer hover:border-yellow-500/30 transition-colors">
                                                    <input type="checkbox"
                                                        checked={form.equipment.includes(opt.value)}
                                                        onChange={() => toggleEquipment(opt.value)}
                                                        className="accent-yellow-500" />
                                                    {opt.label}
                                                </label>
                                            ))}
                                        </div>
                                        <p className="text-xs text-zinc-500">Leave blank if you only train with bodyweight.</p>
                                    </div>
                                    <div className="space-y-3">
                                        <Label>Injuries or Areas to Avoid Stressing</Label>
                                        <div className="grid grid-cols-2 gap-2">
                                            {INJURY_OPTIONS.map(opt => (
                                                <label key={opt.value}
                                                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-zinc-950 border border-white/10 text-sm cursor-pointer hover:border-yellow-500/30 transition-colors">
                                                    <input type="checkbox"
                                                        checked={form.injuries.includes(opt.value)}
                                                        onChange={() => toggleInjury(opt.value)}
                                                        className="accent-yellow-500" />
                                                    {opt.label}
                                                </label>
                                            ))}
                                        </div>
                                        <p className="text-xs text-zinc-500">FitGen will filter out exercises that stress these areas.</p>
                                    </div>
                                </div>
                            )}

                            {step === 5 && (
                                <div className="space-y-4">
                                    <p className="text-sm text-zinc-400">Add YouTube workout videos. FitGen extracts exercises from captions.</p>
                                    <div className="space-y-3">
                                        {form.youtubeUrls.map((url, i) => (
                                            <div key={i} className="flex gap-2 items-center">
                                                <Input placeholder="https://www.youtube.com/watch?v=..." value={url}
                                                    onChange={e => updateUrl(i, e.target.value)} className="flex-1" />
                                                {form.youtubeUrls.length > 1 && (
                                                    <button onClick={() => removeUrl(i)} className="text-zinc-500 hover:text-red-400 transition-colors p-1">
                                                        <X className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                    <button onClick={addUrl} className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-yellow-500 transition-colors">
                                        <Plus className="w-3.5 h-3.5" /> Add another video
                                    </button>
                                </div>
                            )}

                            {step === 6 && (
                                <BodyCompositionStep
                                    heightCm={Number(form.height) || 175}
                                    gender={form.gender}
                                    experienceLevel={form.experience}
                                    pushupCount={form.pushups.trim() ? Number(form.pushups) : undefined}
                                    squatCount={form.squats.trim() ? Number(form.squats) : undefined}
                                    result={result}
                                    onResult={setResult}
                                />
                            )}

                        </motion.div>
                    </AnimatePresence>

                    <div className="mt-10 flex justify-between pt-6 border-t border-white/5">
                        <Button variant="ghost" onClick={() => setStep(p => p - 1)}
                            disabled={step === 0} className={step === 0 ? 'invisible' : ''}>
                            <ArrowLeft className="w-4 h-4 mr-2" /> Back
                        </Button>
                        <Button onClick={handleNext} className="w-32">
                            {step === STEPS.length - 1 ? 'Finish' : 'Next'}
                            {step !== STEPS.length - 1 && <ArrowRight className="w-4 h-4 ml-2" />}
                        </Button>
                    </div>
                </div>
            </main>
        </div>
    );
}
