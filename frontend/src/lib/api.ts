import axios from 'axios';

// ── Local Storage Migration (koda -> fitgen) ──────────────────────────────
if (typeof window !== 'undefined') {
    const oldUser = localStorage.getItem('koda_user');
    if (oldUser && !localStorage.getItem('fitgen_user')) {
        localStorage.setItem('fitgen_user', oldUser);
        localStorage.removeItem('koda_user');
    }

    const oldToken = localStorage.getItem('koda_token');
    if (oldToken && !localStorage.getItem('fitgen_token')) {
        localStorage.setItem('fitgen_token', oldToken);
        localStorage.removeItem('koda_token');
    }

    const oldOnboarded = localStorage.getItem('koda_onboarded');
    if (oldOnboarded && !localStorage.getItem('fitgen_onboarded')) {
        localStorage.setItem('fitgen_onboarded', oldOnboarded);
        localStorage.removeItem('koda_onboarded');
    }

    const oldTheme = localStorage.getItem('koda_theme');
    if (oldTheme && !localStorage.getItem('fitgen_theme')) {
        localStorage.setItem('fitgen_theme', oldTheme);
        localStorage.removeItem('koda_theme');
    }
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('fitgen_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});

api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (typeof window !== 'undefined' && axios.isAxiosError(err) && err.response?.status === 401) {
            localStorage.removeItem('fitgen_token');
            localStorage.removeItem('fitgen_user');
            localStorage.removeItem('fitgen_onboarded');
        }
        return Promise.reject(err);
    }
);

export default api;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type JobStatus = 'pending' | 'running' | 'done' | 'failed';

export interface JobResponse {
    job_id: string;
    status: JobStatus;
    message?: string;
}

export interface JobStatusResponse {
    job_id: string;
    status: JobStatus;
    result?: Record<string, unknown> | null;
    error?: string | null;
}

export interface PlanJobPayload {
    user_profile: Record<string, unknown>;
    workout_youtube_urls?: string[];
    diet_youtube_urls?: string[];
    youtube_urls: string[];
    transcript_text?: string;
}

export type BodyCompositionSource =
    'photo_analysis' | 'photo_plus_manual' | 'tape_measurement' | 'self_assessment' | 'unavailable';

export interface BodyCompositionResult {
    fat_pct_low?: number | null;
    fat_pct_high?: number | null;
    muscle_level?: string | null;
    muscle_level_confidence?: number;
    v_taper_ratio?: number | null;
    posture_assessment?: string | null;
    is_valid_person?: boolean;
    pose_detected?: boolean;
    confidence?: number;
    waist_source?: 'estimated' | 'manual';
    hip_source?: 'estimated' | 'manual';
    source?: BodyCompositionSource;
    input_completeness?: 'full' | 'partial';
    [key: string]: unknown;
}

export type UploadPhotosResult = BodyCompositionResult;

export interface TapeMeasurementPayload {
    neck_cm: number;
    waist_cm: number;
    hip_cm?: number | null;
    height_cm: number;
    gender: 'male' | 'female';
}

export interface SelfAssessmentPayload {
    visible_muscle_separation: 'none' | 'slight' | 'moderate' | 'defined' | 'very_defined';
    vascularity: 'none' | 'slight' | 'moderate' | 'high';
    body_fat_impression: 'not_visible' | 'partially_visible' | 'visible' | 'very_visible';
    perceived_muscle_mass: 'below_average' | 'average' | 'above_average' | 'well_above_average';
    experience_level: 'beginner' | 'intermediate' | 'advanced';
    pushup_count?: number | null;
    squat_count?: number | null;
}

// ---------------------------------------------------------------------------
// Plan job — async Celery dispatch
// ---------------------------------------------------------------------------

export async function submitPlanJob(payload: PlanJobPayload): Promise<JobResponse> {
    try {
        const res = await api.post<JobResponse>('/api/v1/plans/generate', payload);
        return res.data;
    } catch (err) {
        if (axios.isAxiosError(err)) {
            console.error(
                '[submitPlanJob] API error',
                err.response?.status,
                err.response?.data,
                '\nPayload sent:', JSON.stringify(payload, null, 2),
            );
        } else {
            console.error('[submitPlanJob] Network error — is the backend running at', api.defaults.baseURL, err);
        }
        throw err;
    }
}

export async function pollJobStatus(jobId: string): Promise<JobStatusResponse> {
    const res = await api.get<JobStatusResponse>(`/api/v1/plans/job/${jobId}`);
    return res.data;
}

export async function downloadPlanPdf(jobId: string): Promise<Blob> {
    const res = await api.get(`/api/v1/plans/job/${jobId}/pdf`, { responseType: 'blob' });
    return res.data as Blob;
}

// ---------------------------------------------------------------------------
// Vision — 3-photo body composition upload
// ---------------------------------------------------------------------------

export async function uploadPhotos(
    front: File,
    side: File | null | undefined,
    back: File | null | undefined,
    heightCm: number,
    gender: string,
    consent: boolean,
    waistCm?: number | null,
    hipCm?: number | null,
): Promise<UploadPhotosResult> {
    if (!consent) {
        throw new Error('Consent is required before photos can be analysed.');
    }

    const form = new FormData();
    form.append('front', front);
    if (side) form.append('side', side);
    if (back) form.append('back', back);
    form.append('consent', 'true');
    form.append('user_height_cm', String(heightCm));
    form.append('gender', gender);
    if (waistCm !== undefined && waistCm !== null && !Number.isNaN(waistCm)) {
        form.append('waist_cm', String(waistCm));
    }
    if (hipCm !== undefined && hipCm !== null && !Number.isNaN(hipCm)) {
        form.append('hip_cm', String(hipCm));
    }

    const res = await api.post<UploadPhotosResult>(
        '/api/v1/vision/analyze-body',
        form,
        { headers: { 'Content-Type': undefined, 'X-Vision-Consent': 'true' } }
    );
    return res.data;
}

// ---------------------------------------------------------------------------
// Metrics — tape measurement / self-assessment (non-photo body composition)
// ---------------------------------------------------------------------------

export async function submitTapeMeasurement(
    payload: TapeMeasurementPayload
): Promise<BodyCompositionResult> {
    const res = await api.post<BodyCompositionResult>('/api/v1/metrics/tape-measurement', payload);
    return res.data;
}

export async function submitSelfAssessment(
    payload: SelfAssessmentPayload
): Promise<BodyCompositionResult> {
    const res = await api.post<BodyCompositionResult>('/api/v1/metrics/self-assessment', payload);
    return res.data;
}