import numpy as np
import pandas as pd


def _schat_fs(t):
    t = np.asarray(t, dtype=float)
    if len(t) < 2:
        return 100.0
    dt = float(np.median(np.diff(t)))
    return 1.0 / dt if dt > 0 else 100.0


def _apply_min_duration(mask, min_samples):
    """Keep only True-runs with at least min_samples length."""
    mask = np.asarray(mask, dtype=bool)
    out = np.zeros_like(mask, dtype=bool)
    run = 0
    for i, v in enumerate(mask):
        if v:
            run += 1
        else:
            if run >= min_samples:
                out[i - run:i] = True
            run = 0
    if run >= min_samples:
        out[len(mask) - run:len(mask)] = True
    return out


def _mask_to_intervals(mask, t):
    """Convert boolean mask to start/end times."""
    m = np.asarray(mask, dtype=int)
    padded = np.concatenate(([0], m, [0]))
    d = np.diff(padded)
    s_idx = np.where(d == 1)[0]
    e_idx = np.where(d == -1)[0] - 1
    return t[s_idx], t[e_idx]


def _interval_overlap(s1, e1, s2, e2):
    s = max(float(s1), float(s2))
    e = min(float(e1), float(e2))
    return s, e


def _rolling_amp_ratio(signal, t, start_t, end_t, fs, pre_s=5.0, amp_window_s=1.0):
    """
    Ratio amplitude_during / amplitude_before using rolling max-min.
    """
    x = np.asarray(signal, dtype=float)
    t = np.asarray(t, dtype=float)
    pre_mask = (t >= max(float(t[0]), float(start_t) - float(pre_s))) & (t < float(start_t))
    in_mask = (t >= float(start_t)) & (t <= float(end_t))
    if np.sum(pre_mask) < 10 or np.sum(in_mask) < 10:
        return np.nan

    w = max(5, int(float(amp_window_s) * fs))
    pre_amp = (
        pd.Series(x[pre_mask]).rolling(w, min_periods=max(2, w // 5)).max()
        - pd.Series(x[pre_mask]).rolling(w, min_periods=max(2, w // 5)).min()
    )
    in_amp = (
        pd.Series(x[in_mask]).rolling(w, min_periods=max(2, w // 5)).max()
        - pd.Series(x[in_mask]).rolling(w, min_periods=max(2, w // 5)).min()
    )
    pre_val = float(np.nanmedian(pre_amp.to_numpy()))
    in_val = float(np.nanmedian(in_amp.to_numpy()))
    return in_val / (pre_val + 1e-12), pre_val, in_val


def detect_transducer_baseline_shift(
    signal,
    t,
    fs,
    trend_window_s=3.0,
    compare_window_s=3.0,
    min_shift_mmHg=6.0,
    min_duration_s=4.0,
    merge_gap_s=1.0,
    recover_tolerance_mmHg=1.0,
    recover_hold_s=1.0,
    direction="both",
):
    """
    Detect sustained downward baseline shifts while pulsatility can remain.
    """
    x = np.asarray(signal, dtype=float)
    t = np.asarray(t, dtype=float)

    w_trend = max(3, int(trend_window_s * fs))
    trend = (
        pd.Series(x)
        .rolling(window=w_trend, center=True, min_periods=max(1, w_trend // 2))
        .median()
        .bfill()
        .ffill()
        .to_numpy()
    )

    w_cmp = max(3, int(compare_window_s * fs))
    min_samples = max(1, int(min_duration_s * fs))
    recover_hold_samples = max(1, int(recover_hold_s * fs))

    # Step detection using median(before) vs median(after) around each point.
    shift = np.zeros(len(trend), dtype=float)
    for i in range(w_cmp, len(trend) - w_cmp):
        before = float(np.median(trend[i - w_cmp:i]))
        after = float(np.median(trend[i:i + w_cmp]))
        shift[i] = after - before

    if direction == "down":
        candidates = shift <= -float(min_shift_mmHg)
    elif direction == "up":
        candidates = shift >= float(min_shift_mmHg)
    else:
        candidates = np.abs(shift) >= float(min_shift_mmHg)

    candidates = _apply_min_duration(candidates, min_samples=max(1, int(0.5 * fs)))

    # Segment from changepoint until baseline returns near pre-step level.
    mask = np.zeros(len(trend), dtype=bool)
    i = w_cmp
    while i < len(trend):
        if not candidates[i]:
            i += 1
            continue

        # Candidate run bounds
        run_start = i
        run_end = i
        while run_end + 1 < len(candidates) and candidates[run_end + 1]:
            run_end += 1

        # Changepoint close to max step magnitude inside run.
        local = shift[run_start:run_end + 1]
        if len(local) == 0:
            i = run_end + 1
            continue
        cp = run_start + int(np.argmax(np.abs(local)))
        start_idx = cp
        baseline_before = float(np.median(trend[max(0, cp - w_cmp):cp]))
        step_dir = np.sign(shift[cp]) if shift[cp] != 0 else 1.0

        # Hold until trend recovers to pre-step baseline.
        j = max(cp + min_samples, start_idx + min_samples)
        end_idx = len(trend) - 1
        recovered_run = 0
        if step_dir < 0:
            recover_level = baseline_before - float(recover_tolerance_mmHg)
            recovered_check = lambda v: v >= recover_level
        else:
            recover_level = baseline_before + float(recover_tolerance_mmHg)
            recovered_check = lambda v: v <= recover_level
        while j < len(trend):
            if recovered_check(trend[j]):
                recovered_run += 1
                if recovered_run >= recover_hold_samples:
                    end_idx = j - recover_hold_samples + 1
                    break
            else:
                recovered_run = 0
            j += 1

        if end_idx >= start_idx and (end_idx - start_idx + 1) >= min_samples:
            mask[start_idx:end_idx + 1] = True
        i = end_idx + 1

    # Merge brief interior gaps only (avoid boundary artifacts).
    if merge_gap_s > 0 and np.any(mask):
        gap_samples = max(1, int(merge_gap_s * fs))
        m = mask.copy()
        idx = 0
        while idx < len(m):
            if m[idx]:
                idx += 1
                continue
            gap_start = idx
            while idx < len(m) and not m[idx]:
                idx += 1
            gap_end = idx - 1
            gap_len = gap_end - gap_start + 1
            left_true = gap_start > 0 and m[gap_start - 1]
            right_true = idx < len(m) and m[idx]
            if left_true and right_true and gap_len <= gap_samples:
                m[gap_start:gap_end + 1] = True
        mask = m

    if len(mask) > 1:
        mask[0] = False
        mask[-1] = False

    start_t, end_t = _mask_to_intervals(mask, t)
    return mask, start_t, end_t, trend, shift


def functie_transducer(t, ABP, CVP):
    t = np.asarray(t, dtype=float)
    fs = _schat_fs(t)
    rows = []

    _, start_abp, end_abp, _, _ = detect_transducer_baseline_shift(
        signal=ABP,
        t=t,
        fs=fs,
        trend_window_s=3.0,
        compare_window_s=3.0,
        min_shift_mmHg=5.0,
        min_duration_s=3.0,
        merge_gap_s=1.0,
        direction="down",
    )
    _, start_cvp, end_cvp, _, _ = detect_transducer_baseline_shift(
        signal=CVP,
        t=t,
        fs=fs,
        trend_window_s=3.0,
        compare_window_s=3.0,
        min_shift_mmHg=3.0,
        min_duration_s=3.0,
        merge_gap_s=1.0,
        direction="down",
    )
    # Specificity filters from trend analysis:
    # 1) ABP/CVP should start almost together
    # 2) substantial overlap duration
    # 3) pulsation amplitude remains approximately stable in both signals
    min_overlap_s = 20.0
    max_start_diff_s = 1.0
    amp_ratio_min = 0.8
    amp_ratio_max = 1.2
    # Absolute minimum pulsatility to avoid labeling low-amplitude calibration blocks.
    abp_amp_min = 8.0
    cvp_amp_min = 3.0

    for s_abp, e_abp in zip(start_abp, end_abp):
        for s_cvp, e_cvp in zip(start_cvp, end_cvp):
            if abs(float(s_abp) - float(s_cvp)) > max_start_diff_s:
                continue
            s, e = _interval_overlap(s_abp, e_abp, s_cvp, e_cvp)
            if e <= s or (e - s) < min_overlap_s:
                continue

            abp_ratio, abp_pre_amp, abp_in_amp = _rolling_amp_ratio(ABP, t, s, e, fs=fs, pre_s=5.0, amp_window_s=1.0)
            cvp_ratio, cvp_pre_amp, cvp_in_amp = _rolling_amp_ratio(CVP, t, s, e, fs=fs, pre_s=5.0, amp_window_s=1.0)
            if np.isnan(abp_ratio) or np.isnan(cvp_ratio):
                continue
            if not (amp_ratio_min <= abp_ratio <= amp_ratio_max):
                continue
            if not (amp_ratio_min <= cvp_ratio <= amp_ratio_max):
                continue
            if min(abp_pre_amp, abp_in_amp) < abp_amp_min:
                continue
            if min(cvp_pre_amp, cvp_in_amp) < cvp_amp_min:
                continue

            rows.append([f"{s:.2f}", f"{e:.2f}", "Transducer Hoog", "ABP"])
            rows.append([f"{s:.2f}", f"{e:.2f}", "Transducer Hoog", "CVP"])

    if not rows:
        return pd.DataFrame(columns=["Starttijd", "Eindtijd", "Naam", "Signaal"])
    return (
        pd.DataFrame(rows, columns=["Starttijd", "Eindtijd", "Naam", "Signaal"])
        .drop_duplicates()
        .reset_index(drop=True)
    )
