import numpy as np
import pandas as pd

from artefacten.gasbel import functie_gasbel
from artefacten.slinger import functie_slinger
from artefacten.flush import functie_flush
from artefacten.calibratie import functie_calibratie
from artefacten.transducer import functie_transducer
from artefacten.infuus import functie_CVD



def leeg_df():
    return pd.DataFrame(
        columns=["Starttijd", "Eindtijd", "Naam van het artefact", "Signaal"]
    )


def niet_leeg(df):
    return df is not None and not df.empty


def overlap(interval_a_start, interval_a_end, interval_b_start, interval_b_end):
    """True als twee intervallen overlap hebben."""
    return not (interval_a_start > interval_b_end or interval_a_end < interval_b_start)


def volledig_binnen(inner_start, inner_end, outer_start, outer_end):
    """True als interval inner volledig binnen outer ligt."""
    return inner_start > outer_start and inner_end < outer_end


def filter_overlap_df(df_hoofd, df_prioriteit, signalen=None, volledig=False):
    """
    Verwijder rijen uit df_hoofd als ze overlappen met df_prioriteit.

    Parameters
    ----------
    df_hoofd : DataFrame
        De artefacten die eventueel verwijderd moeten worden.
    df_prioriteit : DataFrame
        De artefacten met voorrang.
    signalen : list[str] of None
        Bijvoorbeeld ["ABP", "CVP"] of alleen ["CVP"].
    volledig : bool
        Als True: alleen verwijderen als interval volledig binnen prioriteitsinterval valt.
        Als False: verwijderen bij elke overlap.
    """
    if not niet_leeg(df_hoofd) or not niet_leeg(df_prioriteit):
        return df_hoofd.copy()

    df_result = df_hoofd.copy()

    if signalen is not None:
        df_result = df_result[df_result["Signaal"].isin(signalen)].copy()
        df_rest = df_hoofd[~df_hoofd["Signaal"].isin(signalen)].copy()
    else:
        df_rest = leeg_df()

    rows_to_keep = []

    for _, row in df_result.iterrows():
        start_a = row["Starttijd"]
        end_a = row["Eindtijd"]
        signaal = row["Signaal"]

        prior_rows = df_prioriteit[df_prioriteit["Signaal"] == signaal]

        verwijderen = False
        for _, prow in prior_rows.iterrows():
            start_b = prow["Starttijd"]
            end_b = prow["Eindtijd"]

            if volledig:
                if volledig_binnen(start_a, end_a, start_b, end_b):
                    verwijderen = True
                    break
            else:
                if overlap(start_a, end_a, start_b, end_b):
                    verwijderen = True
                    break

        if not verwijderen:
            rows_to_keep.append(row)

    df_filtered = pd.DataFrame(rows_to_keep, columns=df_result.columns)

    if signalen is not None:
        df_filtered = pd.concat([df_filtered, df_rest], ignore_index=True)

    return df_filtered.sort_values(["Starttijd", "Eindtijd"]).reset_index(drop=True)


def behoud_alleen_signaal(df, signaal):
    if not niet_leeg(df):
        return leeg_df()
    return df[df["Signaal"] == signaal].copy().reset_index(drop=True)


import numpy as np
import pandas as pd


def leeg_df():
    return pd.DataFrame(
        columns=["Starttijd", "Eindtijd", "Naam van het artefact", "Signaal"]
    )


def niet_leeg(df):
    return df is not None and not df.empty


def overlap(interval_a_start, interval_a_end, interval_b_start, interval_b_end):
    """True als twee intervallen overlap hebben."""
    return not (interval_a_start > interval_b_end or interval_a_end < interval_b_start)


def volledig_binnen(inner_start, inner_end, outer_start, outer_end):
    """True als interval inner volledig binnen outer ligt."""
    return inner_start > outer_start and inner_end < outer_end


def filter_overlap_df(df_hoofd, df_prioriteit, signalen=None, volledig=False):
    """
    Verwijder rijen uit df_hoofd als ze overlappen met df_prioriteit.

    Parameters
    ----------
    df_hoofd : DataFrame
        De artefacten die eventueel verwijderd moeten worden.
    df_prioriteit : DataFrame
        De artefacten met voorrang.
    signalen : list[str] of None
        Bijvoorbeeld ["ABP", "CVP"] of alleen ["CVP"].
    volledig : bool
        Als True: alleen verwijderen als interval volledig binnen prioriteitsinterval valt.
        Als False: verwijderen bij elke overlap.
    """
    if not niet_leeg(df_hoofd) or not niet_leeg(df_prioriteit):
        return df_hoofd.copy()

    df_result = df_hoofd.copy()

    if signalen is not None:
        df_result = df_result[df_result["Signaal"].isin(signalen)].copy()
        df_rest = df_hoofd[~df_hoofd["Signaal"].isin(signalen)].copy()
    else:
        df_rest = leeg_df()

    rows_to_keep = []

    for _, row in df_result.iterrows():
        start_a = row["Starttijd"]
        end_a = row["Eindtijd"]
        signaal = row["Signaal"]

        prior_rows = df_prioriteit[df_prioriteit["Signaal"] == signaal]

        verwijderen = False
        for _, prow in prior_rows.iterrows():
            start_b = prow["Starttijd"]
            end_b = prow["Eindtijd"]

            if volledig:
                if volledig_binnen(start_a, end_a, start_b, end_b):
                    verwijderen = True
                    break
            else:
                if overlap(start_a, end_a, start_b, end_b):
                    verwijderen = True
                    break

        if not verwijderen:
            rows_to_keep.append(row)

    df_filtered = pd.DataFrame(rows_to_keep, columns=df_result.columns)

    if signalen is not None:
        df_filtered = pd.concat([df_filtered, df_rest], ignore_index=True)

    return df_filtered.sort_values(["Starttijd", "Eindtijd"]).reset_index(drop=True)


def behoud_alleen_signaal(df, signaal):
    if not niet_leeg(df):
        return leeg_df()
    return df[df["Signaal"] == signaal].copy().reset_index(drop=True)


def functie_prioriteitcalibratie_slinger(t, ABP, CVP, fs=100):
    artefacten_uit_calibratie, *_ = functie_calibratie(t, ABP, CVP, fs=fs)
    artefacten_uit_slinger, *_ = functie_slinger(t, ABP, CVP, fs=fs)

    if niet_leeg(artefacten_uit_calibratie) and niet_leeg(artefacten_uit_slinger):
        artefacten_uit_slinger = filter_overlap_df(
            df_hoofd=artefacten_uit_slinger,
            df_prioriteit=artefacten_uit_calibratie,
            signalen=["ABP", "CVP"],
            volledig=False,
        )

    return artefacten_uit_slinger


def functie_prioriteitflush(t, ABP, CVP, fs=100):
    artefacten_uit_flush, *_ = functie_flush(t, ABP, CVP, fs=fs)
    artefacten_uit_slinger, *_ = functie_slinger(t, ABP, CVP, fs=fs)

    if niet_leeg(artefacten_uit_flush) and niet_leeg(artefacten_uit_slinger):
        artefacten_uit_slinger = filter_overlap_df(
            df_hoofd=artefacten_uit_slinger,
            df_prioriteit=artefacten_uit_flush,
            signalen=["ABP", "CVP"],
            volledig=False,
        )
    else:
        artefacten_uit_slinger = leeg_df()

    return artefacten_uit_slinger


def functie_prioriteitflushCVD(t, ABP, CVP, fs=100):
    artefacten_uit_flush, *_ = functie_flush(t, ABP, CVP, fs=fs)
    artefacten_uit_CVD, *_ = functie_CVD(t, ABP, CVP, fs=fs)

    if niet_leeg(artefacten_uit_flush) and niet_leeg(artefacten_uit_CVD):
        artefacten_uit_CVD = filter_overlap_df(
            df_hoofd=artefacten_uit_CVD,
            df_prioriteit=artefacten_uit_flush,
            signalen=["ABP", "CVP"],
            volledig=False,
        )
    else:
        artefacten_uit_CVD = leeg_df()

    return artefacten_uit_CVD

def functie_prioriteitflushovertransducer(t, ABP, CVP, fs=100):
    artefacten_uit_transducer, *_ = functie_transducer(t, ABP, CVP, fs=fs)
    artefacten_uit_flush, *_ = functie_flush(t, ABP, CVP, fs=fs)

    if niet_leeg(artefacten_uit_transducer) and niet_leeg(artefacten_uit_flush):
        artefacten_uit_transducer = filter_overlap_df(
            df_hoofd=artefacten_uit_transducer,
            df_prioriteit=artefacten_uit_flush,
            signalen=["ABP", "CVP"],
            volledig=True,
        )
    else:
        artefacten_uit_transducer = leeg_df()

    return artefacten_uit_transducer

def functie_prioriteitscalibratie(t, ABP, CVP, fs=100):
    artefacten_uit_gasbel, *_ = functie_gasbel(t, ABP, CVP, fs=fs)
    artefacten_uit_calibratie, *_ = functie_calibratie(t, ABP, CVP, fs=fs)

    if niet_leeg(artefacten_uit_gasbel) and niet_leeg(artefacten_uit_calibratie):
        artefacten_uit_gasbel = filter_overlap_df(
            df_hoofd=artefacten_uit_gasbel,
            df_prioriteit=artefacten_uit_calibratie,
            signalen=["ABP", "CVP"],
            volledig=False,
        )
    else:
        artefacten_uit_gasbel = leeg_df()

    return artefacten_uit_gasbel

def functie_prioriteitslinger(t, ABP, CVP, fs=100):
    artefacten_uit_flush, *_ = functie_flush(t, ABP, CVP, fs=fs)
    artefacten_uit_slinger, *_ = functie_slinger(t, ABP, CVP, fs=fs)

    if niet_leeg(artefacten_uit_flush) and niet_leeg(artefacten_uit_slinger):
        artefacten_uit_flush = filter_overlap_df(
            df_hoofd=artefacten_uit_flush,
            df_prioriteit=artefacten_uit_slinger,
            signalen=["ABP", "CVP"],
            volledig=True,
        )
    else:
        artefacten_uit_flush = leeg_df()

    return artefacten_uit_flush

def functie_prioriteitCVD_slinger(t, ABP, CVP, fs=100):
    artefacten_uit_CVD, *_ = functie_CVD(t, ABP, CVP, fs=fs)
    artefacten_uit_slinger, *_ = functie_slinger(t, ABP, CVP, fs=fs)

    if niet_leeg(artefacten_uit_CVD) and niet_leeg(artefacten_uit_slinger):
        artefacten_uit_slinger = filter_overlap_df(
            df_hoofd=artefacten_uit_slinger,
            df_prioriteit=artefacten_uit_CVD,
            signalen=["CVP"],   # alleen CVP verwijderen
            volledig=False,
        )

    return artefacten_uit_slinger