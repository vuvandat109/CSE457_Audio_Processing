"""CSE457 Lab 5: enhancement, speaker recognition and source separation."""
from pathlib import Path
import csv
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.fft import dct
from scipy.io import wavfile
from sklearn.decomposition import FastICA
from sklearn.metrics import confusion_matrix

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "lab5_data"
AUDIO = ROOT / "results/audio"
FIGURES = ROOT / "results/figures"
CONFIG = {
    "sr": 16000, "window": 400, "hop": 160, "nfft": 512, "seed": 457,
    "snrs": [0, 5, 10], "betas": [1, 1.5, 2], "floors": [0, .01, .05],
    "beta": 1.5, "floor": .01, "n_mel": 40, "n_mfcc": 20,
    "mixing": {"easy": [[1, .6], [.4, 1]], "near_singular": [[1, .97], [.98, 1]]},
    "mixture_noise_snr": 25,
}
SR = CONFIG["sr"]
EPS = 1e-12


def load(path):
    rate, samples = wavfile.read(path)
    if np.issubdtype(samples.dtype, np.unsignedinteger):
        midpoint = (np.iinfo(samples.dtype).max + 1) / 2
        samples = (samples.astype(float) - midpoint) / midpoint
    elif np.issubdtype(samples.dtype, np.signedinteger):
        samples = samples.astype(float) / abs(np.iinfo(samples.dtype).min)
    if samples.ndim == 2:
        samples = samples.mean(axis=1)
    if rate != SR:
        divisor = math.gcd(SR, rate)
        samples = signal.resample_poly(samples, SR // divisor, rate // divisor)
    return samples


def write_audio(name, samples):
    if np.max(np.abs(samples)) > 1:
        raise ValueError(f"Audio would clip: {name}")
    wavfile.write(AUDIO / (name + ".wav"), SR,
                  np.round(samples * 32767).astype(np.int16))


def csv_table(name, rows):
    with (ROOT / "results" / (name + ".csv")).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def power(samples):
    return np.mean(samples ** 2)


def snr(reference, estimate):
    return float(10 * np.log10(max(power(reference), EPS) /
                               max(power(reference - estimate), EPS)))


def add_noise(clean, noise, target):
    segment = np.resize(noise, len(clean))
    if power(segment) < EPS or power(clean) < EPS:
        raise ValueError("SNR requires non-silent speech and noise")
    alpha = np.sqrt(power(clean) / (power(segment) * 10 ** (target / 10)))
    return clean + alpha * segment, alpha


def transform(samples):
    return signal.stft(samples, fs=SR, window="hann", nperseg=CONFIG["window"],
                       noverlap=CONFIG["window"] - CONFIG["hop"], nfft=CONFIG["nfft"])


def inverse(spectrum, length):
    _, audio = signal.istft(spectrum, fs=SR, window="hann", nperseg=CONFIG["window"],
                            noverlap=CONFIG["window"] - CONFIG["hop"], nfft=CONFIG["nfft"])
    return audio[:length]


def enhance(noisy, noise_reference, alpha, beta=CONFIG["beta"], floor=CONFIG["floor"]):
    _, _, observed = transform(noisy)
    _, _, noise_stft = transform(alpha * noise_reference)
    noise_psd = np.mean(abs(noise_stft[:, 1:-1]) ** 2, axis=1, keepdims=True)
    observed_power = abs(observed) ** 2
    ss_power = np.maximum(observed_power - beta * noise_psd, floor * noise_psd)
    ss = np.sqrt(ss_power) * np.exp(1j * np.angle(observed))
    estimated = np.maximum(observed_power - noise_psd, 0)
    wiener = observed * estimated / (estimated + noise_psd + EPS)
    return inverse(ss, len(noisy)), inverse(wiener, len(noisy))


def save_figure(fig, name):
    fig.savefig(FIGURES / (name + ".png"), dpi=145, bbox_inches="tight")
    plt.close(fig)


def compare_audio(series, name):
    fig, axes = plt.subplots(len(series), 2, figsize=(9, 1.9 * len(series)),
                             layout="constrained", squeeze=False)
    ceiling = max(np.max(abs(samples)) for _, samples in series)
    for (label, samples), (wave, spectrum) in zip(series, axes):
        time = np.arange(len(samples)) / SR
        wave.plot(time, samples, linewidth=.6, color="#166b88")
        wave.set(xlim=(0, time[-1]), ylim=(-ceiling, ceiling), ylabel=label, xlabel="Time (s)")
        f, t, z = transform(samples)
        image = spectrum.pcolormesh(t, f, 20 * np.log10(abs(z) + EPS),
                                    vmin=-90, vmax=-22, shading="auto", cmap="magma")
        spectrum.set(ylim=(0, 6500), xlabel="Time (s)", ylabel="Hz")
    fig.colorbar(image, ax=axes[:, 1], label="dB")
    save_figure(fig, name)


def enhancement_experiments(clean, fan):
    noise_clip = fan[-2 * SR:]
    rows = []
    for target in CONFIG["snrs"]:
        noisy, alpha = add_noise(clean, fan, target)
        measured = snr(clean, noisy)
        assert abs(measured - target) <= .2
        baseline_ss, wiener = enhance(noisy, noise_clip, alpha)
        for beta in CONFIG["betas"]:
            for floor in CONFIG["floors"]:
                enhanced, _ = enhance(noisy, noise_clip, alpha, beta, floor)
                rows.append(dict(target_db=target, measured_db=measured, beta=beta,
                                 floor=floor, clean_power=power(clean), clean_rms=np.sqrt(power(clean)),
                                 noise_power=power(fan[:len(clean)]),
                                 noise_rms=np.sqrt(power(fan[:len(clean)])), alpha=alpha,
                                 ss_out_db=snr(clean, enhanced), ss_gain_db=snr(clean, enhanced)-measured,
                                 wiener_out_db=snr(clean, wiener),
                                 wiener_gain_db=snr(clean, wiener)-measured))
                if target == 5:
                    write_audio(f"ablation/ss_beta{beta}_floor{floor}", enhanced)
        for label, samples in [("clean", clean), ("noisy", noisy),
                               ("enhanced_ss", baseline_ss), ("enhanced_wiener", wiener)]:
            if label != "clean":
                write_audio(f"{label}_{target}db", samples)
            if target == 5:
                write_audio(label, samples)
        compare_audio([("Clean", clean), ("Noisy", noisy), ("SS", baseline_ss),
                       ("Wiener", wiener)], f"spectrogram_{target}db")
    csv_table("enhancement", rows)


def enhancement_diagnostics(clean, fan):
    """Compare residual background and active-speech error on the reference clip."""
    frames = len(clean) // CONFIG["window"]
    shape = (frames, CONFIG["window"])
    reference = clean[:frames * CONFIG["window"]].reshape(shape)
    frame_power = np.mean(reference ** 2, axis=1)
    quiet = frame_power <= .001 * frame_power.max()
    active = frame_power >= .03 * frame_power.max()
    rows = []
    for target in CONFIG["snrs"]:
        noisy, alpha = add_noise(clean, fan, target)
        ss, wiener = enhance(noisy, fan[-2 * SR:], alpha)
        for label, samples in [("noisy", noisy), ("ss", ss), ("wiener", wiener)]:
            error = samples[:reference.size].reshape(shape) - reference
            rows.append(dict(target_db=target, method=label,
                             quiet_frames=int(quiet.sum()), active_frames=int(active.sum()),
                             quiet_error_rms=float(np.sqrt(power(error[quiet]))) if quiet.any() else "",
                             active_error_rms=float(np.sqrt(power(error[active]))) if active.any() else ""))
    csv_table("enhancement_frame_diagnostics", rows)


def mel_filters():
    frequencies = np.fft.rfftfreq(CONFIG["nfft"], 1 / SR)
    mel_edges = np.linspace(0, 2595 * np.log10(1 + (SR / 2) / 700),
                            CONFIG["n_mel"] + 2)
    edges = 700 * (10 ** (mel_edges / 2595) - 1)
    left = (frequencies - edges[:-2, None]) / np.diff(edges)[:-1, None]
    right = (edges[2:, None] - frequencies) / np.diff(edges)[1:, None]
    return np.maximum(0, np.minimum(left, right))


MEL = mel_filters()


def embedding(samples, delta=True, cmn=False):
    emphasized = signal.lfilter([1, -.97], [1], samples)
    _, _, spectrum = transform(emphasized)
    energies = np.sum(abs(spectrum) ** 2, axis=0)
    # Drop low-energy frames so silence has less influence on pooled statistics.
    active = energies > .002 * energies.max()
    cepstra = dct(np.log(MEL @ abs(spectrum) ** 2 + EPS), type=2, axis=0, norm="ortho")
    cepstra = cepstra[1:CONFIG["n_mfcc"] + 1]
    if cmn:
        cepstra = cepstra - cepstra[:, active].mean(axis=1, keepdims=True)
    features = [cepstra]
    if delta:
        features.append(signal.savgol_filter(cepstra, 5, 2, deriv=1, axis=1))
    vector = np.concatenate([stat(feature[:, active], axis=1)
                             for feature in features for stat in (np.mean, np.std)])
    return vector / max(np.linalg.norm(vector), EPS)


def models_for(enroll, tokens=4, **settings):
    models = np.array([np.mean([embedding(x, **settings) for x in items[:tokens]], axis=0)
                       for items in enroll.values()])
    return models / np.linalg.norm(models, axis=1, keepdims=True)


def identification(examples, models, speakers, **settings):
    scores = np.array([models @ embedding(x, **settings) for _, _, x in examples])
    truth = np.array([speakers.index(label) for _, label, _ in examples])
    predicted = scores.argmax(axis=1)
    margins = np.array([row[i] - np.max(np.delete(row, i)) for i, row in zip(truth, scores)])
    return scores, truth, predicted, float(np.mean(truth == predicted)), float(margins.mean())


def matrix_figure(matrix, rows, columns, title, name, decimals=0):
    fig, ax = plt.subplots(figsize=(4.6, 3.6), layout="constrained")
    image = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=max(1, matrix.max()))
    for i, j in np.ndindex(matrix.shape):
        ax.text(j, i, f"{matrix[i, j]:.{decimals}f}", ha="center", va="center",
                color="white" if matrix[i, j] > .58 * matrix.max() else "#152839")
    ax.set(xticks=range(len(columns)), xticklabels=columns, yticks=range(len(rows)),
           yticklabels=rows, title=title, xlabel="Prediction / estimate", ylabel="Reference")
    fig.colorbar(image, ax=ax)
    save_figure(fig, name)


def verification(dev, test, models, speakers):
    dev_scores, dev_truth, *_ = identification(dev, models, speakers)
    dev_same = dev_truth[:, None] == np.arange(len(speakers))

    def rates(scores, same, threshold):
        return np.mean(scores[~same] >= threshold), np.mean(scores[same] < threshold)

    values = np.unique(dev_scores)
    thresholds = np.r_[np.nextafter(values[0], -np.inf),
                       (values[:-1] + values[1:]) / 2,
                       np.nextafter(values[-1], np.inf)]
    far, frr = np.array([rates(dev_scores, dev_same, t) for t in thresholds]).T
    best = np.lexsort((far + frr, abs(far - frr)))[0]
    threshold = thresholds[best]
    test_scores, test_truth, *_ = identification(test, models, speakers)
    test_same = test_truth[:, None] == np.arange(len(speakers))
    test_far, test_frr = rates(test_scores, test_same, threshold)
    csv_table("verification_dev_curve", [dict(threshold=t, far=a, frr=b)
              for t, a, b in zip(thresholds, far, frr)])
    trial_rows = []
    for split, examples, scores, same in [("dev", dev, dev_scores, dev_same),
                                           ("test", test, test_scores, test_same)]:
        for (filename, actual, _), row, matching in zip(examples, scores, same):
            for claim, score, genuine in zip(speakers, row, matching):
                trial_rows.append(dict(split=split, file=filename, actual=actual, claim=claim,
                                       score=score, genuine=int(genuine),
                                       accepted=int(score >= threshold)))
    csv_table("verification_trials", trial_rows)
    fig, ax = plt.subplots(figsize=(7, 3.4), layout="constrained")
    ax.plot(thresholds, far, "o-", label="FAR (dev)", markersize=3)
    ax.plot(thresholds, frr, "o-", label="FRR (dev)", markersize=3)
    ax.axvline(threshold, linestyle="--", color="gray", label=f"Locked threshold {threshold:.4f}")
    ax.set(xlabel="Cosine threshold", ylabel="Error rate", ylim=(-.05, 1.05))
    ax.legend()
    save_figure(fig, "far_frr")
    return dict(threshold=float(threshold), dev_far=float(far[best]), dev_frr=float(frr[best]),
                test_far=float(test_far), test_frr=float(test_frr),
                test_genuine=int(test_same.sum()), test_impostor=int((~test_same).sum()))


def recognition_experiments(fan):
    paths = sorted((DATA / "clean").glob("spk*_*.wav"))
    speakers = sorted({path.stem.split("_")[0] for path in paths})

    def split_examples(split):
        return [(p.name, p.stem.split("_")[0], load(p)) for p in paths
                if p.stem.split("_")[1] == split]

    enroll = {speaker: [x for _, label, x in split_examples("enroll") if label == speaker]
              for speaker in speakers}
    assert len(speakers) >= 3 and all(len(items) >= 4 for items in enroll.values())
    dev, test = split_examples("dev"), split_examples("test")
    models = models_for(enroll)
    np.savez(ROOT / "results/speaker_models.npz", speaker_labels=speakers, centroids=models)
    condition_examples = {"clean": test}
    for target in CONFIG["snrs"]:
        for label in ("noisy", "ss", "wiener"):
            condition_examples[f"{label}_{target}db"] = []
        for index, (filename, speaker, clean) in enumerate(test):
            noisy, alpha = add_noise(clean, np.roll(fan[:-2 * SR], 311 * index), target)
            ss, wiener = enhance(noisy, fan[-2 * SR:], alpha)
            for label, audio in [("noisy", noisy), ("ss", ss), ("wiener", wiener)]:
                condition_examples[f"{label}_{target}db"].append((filename, speaker, audio))

    audio_metrics = []
    for condition, examples in condition_examples.items():
        if condition == "clean":
            continue
        for (filename, speaker, clean), (_, _, processed) in zip(test, examples):
            measured = snr(clean, processed)
            target = int(condition.split("_")[-1].removesuffix("db"))
            audio_metrics.append(dict(condition=condition, file=filename, speaker=speaker,
                                      target_db=target, actual_db=measured,
                                      improvement_db=measured-target))
    csv_table("enhancement_test_clips", audio_metrics)

    comparison, details = [], []
    for label, examples in condition_examples.items():
        scores, truth, predicted, accuracy, margin = identification(examples, models, speakers)
        comparison.append(dict(condition=label, accuracy=accuracy, mean_margin=margin))
        for (filename, actual, _), guess, row in zip(examples, predicted, scores):
            details.append(dict(condition=label, file=filename, actual=actual,
                                predicted=speakers[guess], **dict(zip(speakers, row))))
        if label == "clean":
            matrix_figure(confusion_matrix(truth, predicted, labels=np.arange(len(speakers))),
                          speakers, speakers, "Speaker identification (clean test)", "confusion_matrix")

    ablation = []
    for delta in (False, True):
        for cmn in (False, True):
            for tokens in (1, 2, 4):
                settings = dict(delta=delta, cmn=cmn)
                _, _, _, acc, margin = identification(test, models_for(enroll, tokens, **settings),
                                                      speakers, **settings)
                ablation.append(dict(delta=delta, cmn=cmn, enrollment_tokens=tokens,
                                     accuracy=acc, mean_margin=margin))
    csv_table("speaker_scores", details)
    csv_table("speaker_conditions", comparison)
    csv_table("speaker_ablation", ablation)
    return verification(dev, test, models, speakers)


def si_sdr(reference, estimate):
    reference = reference - reference.mean()
    estimate = estimate - estimate.mean()
    projection = reference * np.dot(reference, estimate) / np.dot(reference, reference)
    return float(10 * np.log10(max(power(projection), EPS) /
                               max(power(estimate - projection), EPS)))


def separation_experiments():
    sources = [load(DATA / "separation" / f"source_{label}.wav") for label in "AB"]
    length = min(map(len, sources))
    sources = np.array([x[:length] * .055 / np.sqrt(power(x[:length])) for x in sources])
    rng = np.random.default_rng(CONFIG["seed"])
    noises = rng.standard_normal(sources.shape)
    rows = []
    for name, matrix in CONFIG["mixing"].items():
        matrix = np.array(matrix)
        clean_mix = matrix @ sources
        for noisy in (False, True):
            mixtures = np.array([add_noise(mix, noise, CONFIG["mixture_noise_snr"])[0]
                                 for mix, noise in zip(clean_mix, noises)]) if noisy else clean_mix
            # ICA gets only microphone observations. References are used after fitting.
            ica = FastICA(n_components=2, whiten="unit-variance", random_state=CONFIG["seed"],
                          max_iter=2000, tol=1e-5)
            raw = ica.fit_transform(mixtures.T).T
            corr = np.corrcoef(sources, raw)[:2, 2:]
            diagonal_score = abs(corr[0, 0]) + abs(corr[1, 1])
            swapped_score = abs(corr[0, 1]) + abs(corr[1, 0])
            order = [1, 0] if swapped_score > diagonal_score else [0, 1]
            signs = np.where(corr[np.arange(2), order] < 0, -1, 1)
            estimates = raw[order] * signs[:, None] * .055
            matched = np.corrcoef(sources, estimates)[:2, 2:]
            rows.append(dict(matrix=name, noisy=noisy, det=float(np.linalg.det(matrix)),
                             condition_number=float(np.linalg.cond(matrix)), iterations=ica.n_iter_,
                             mic1_a_si_sdr_db=si_sdr(sources[0], mixtures[0]),
                             mic2_b_si_sdr_db=si_sdr(sources[1], mixtures[1]),
                             separated_a_si_sdr_db=si_sdr(sources[0], estimates[0]),
                             separated_b_si_sdr_db=si_sdr(sources[1], estimates[1]),
                             before_11=abs(corr[0, 0]), before_12=abs(corr[0, 1]),
                             before_21=abs(corr[1, 0]), before_22=abs(corr[1, 1]),
                             after_11=abs(matched[0, 0]), after_12=abs(matched[0, 1]),
                             after_21=abs(matched[1, 0]), after_22=abs(matched[1, 1])))
            if name != "easy" or noisy:
                suffix = f"{name}_{'noisy' if noisy else 'clean'}"
                for index, (mix, separated) in enumerate(zip(mixtures, estimates), 1):
                    write_audio(f"ablation/{suffix}_mix_mic{index}", mix)
                    write_audio(f"ablation/{suffix}_separated_{index}", separated)
            if name == "easy" and not noisy:
                for index, (mix, separated) in enumerate(zip(mixtures, estimates), 1):
                    write_audio(f"mix_mic{index}", mix)
                    write_audio(f"separated_{index}", separated)
                for label, values in [("before", corr), ("after", matched)]:
                    matrix_figure(abs(values), ["Source A", "Source B"], ["Output 1", "Output 2"],
                                  f"ICA |correlation| ({label} matching)", f"ica_correlation_{label}", 3)
                compare_audio([("Mic 1", mixtures[0]), ("Mic 2", mixtures[1]),
                               ("Source A est.", estimates[0]), ("Source B est.", estimates[1])],
                              "ica_waveforms")
    csv_table("ica", rows)


def main():
    for folder in (AUDIO / "ablation", FIGURES):
        folder.mkdir(parents=True, exist_ok=True)
    fan = load(DATA / "noise/fan.wav")
    sample = load(DATA / "clean/spk01_test_01.wav")
    sample *= min(1.0, .45 / np.max(abs(sample)))
    enhancement_experiments(sample, fan)
    enhancement_diagnostics(sample, fan)
    verification_result = recognition_experiments(fan)
    separation_experiments()
    summary = {"config": CONFIG, "verification": verification_result}
    (ROOT / "results/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(verification_result, indent=2))
    print("Lab 5 complete. See results/ for WAV, PNG, CSV and JSON.")


if __name__ == "__main__":
    main()
