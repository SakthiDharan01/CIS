import librosa
import numpy as np


class AudioAnalyzer:
    def analyze(self, file_path):
        details = []
        score = 100

        try:
            y, sr = librosa.load(file_path, sr=None, mono=True)
            duration = librosa.get_duration(y=y, sr=sr)
            details.append(f"Duration: {duration:.2f}s @ {sr}Hz")

            # 1. Pitch stability
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[magnitudes > np.median(magnitudes)]
            if len(pitch_values) > 0:
                pitch_std = np.std(pitch_values)
                details.append(f"Pitch std: {pitch_std:.2f}")
                if pitch_std < 10:
                    score -= 20
                    details.append("Pitch is unnaturally stable (synthetic voice likelihood).")

            # 2. Pause timing randomness
            non_silent = librosa.effects.split(y, top_db=25)
            pause_durations = []
            for i in range(len(non_silent) - 1):
                pause_start = non_silent[i][1]
                pause_end = non_silent[i + 1][0]
                pause_durations.append((pause_end - pause_start) / sr)
            if pause_durations:
                avg_pause = np.mean(pause_durations)
                std_pause = np.std(pause_durations)
                details.append(f"Pause avg/std: {avg_pause:.2f}/{std_pause:.2f}s")
                if std_pause < 0.05:
                    score -= 15
                    details.append("Pause timing is too regular (AI-style pacing).")

            # 3. Spectral flatness (too flat -> synthetic)
            flatness = librosa.feature.spectral_flatness(y=y)
            flat_mean = float(np.mean(flatness))
            details.append(f"Spectral flatness mean: {flat_mean:.3f}")
            if flat_mean > 0.35:
                score -= 10
                details.append("Spectrum is very flat (lack of natural formants/breath).")

            # 4. Spectral flux stability (long-range spectral stability)
            stft = np.abs(librosa.stft(y))
            flux = librosa.onset.onset_strength(S=stft, sr=sr)
            flux_std = float(np.std(flux))
            details.append(f"Spectral flux std: {flux_std:.2f}")
            if flux_std < 5:
                score -= 10
                details.append("Spectral changes are overly consistent (possible synthesis).")

            # 5. Breath/micro-burst proxy via RMS spikes
            rms = librosa.feature.rms(S=stft)
            rms_values = rms.flatten()
            spike_ratio = np.sum(rms_values > (np.mean(rms_values) + 2 * np.std(rms_values))) / len(rms_values)
            details.append(f"RMS spike ratio: {spike_ratio:.3f}")
            if spike_ratio < 0.02:
                score -= 5
                details.append("Few micro-bursts (breath/noise) detected (over-clean audio).")

        except Exception as e:
            details.append(f"Error in audio analysis: {str(e)}")
            score -= 10

        return {
            "layer": "Content-Specific AI Pattern Integrity (Audio)",
            "score": max(0, score),
            "details": details
        }
