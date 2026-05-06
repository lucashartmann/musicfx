import numpy as np
from .amplificador import Amplificador


class MarshallPlexiSuperLead1959(Amplificador):
    def __init__(self, sample_rate: int = 48000):
        super().__init__("Marshall Plexi Super Lead 1959", sample_rate)
        self.canal = 'bright'
        self._v1_hp_z = np.zeros(1)
        self._bright_z = np.zeros(1)
        self._v2a_hp_z = np.zeros(1)
        self._v2b_hp_z = np.zeros(1)
        self._ts_bass_z = np.zeros(1)
        self._ts_mid_z = np.zeros(2)
        self._ts_treble_z = np.zeros(2)
        self._pi_hp_z = np.zeros(1)
        self._ot_lp_z = np.zeros(1)
        self._ot_bump_z = np.zeros(2)
        self._pres_z = np.zeros(2)

    def set_canal(self, canal: str):
        if canal not in ('bright', 'normal'):
            raise ValueError("canal deve ser 'bright' ou 'normal'")
        self.canal = canal

    def _preamp(self, samples: np.ndarray) -> np.ndarray:
        fs = self.sample_rate
        fc_v1 = 1.0 / (2.0 * np.pi * 0.022e-6 * 1e6)
        b, a = self._bilinear_hp(fc_v1, fs)
        s, self._v1_hp_z = self._lfilter(b, a, samples, self._v1_hp_z)
        s = self._triode_ecc83(s, gain=60.0, vp_norm=0.9, knee=0.6)
        if self.canal == 'bright':
            fc_bright = 480.0
            b_br, a_br = self._bilinear_hp(fc_bright, fs)
            s_bright, self._bright_z = self._lfilter(
                b_br, a_br, s, self._bright_z)
            bright_mix = 0.35 * self.volume
            s = s + s_bright * bright_mix
        s = s * self.volume
        s = self._triode_ecc83(s, gain=45.0, vp_norm=1.0, knee=0.65)
        fc_v2a = 1.0 / (2.0 * np.pi * 0.022e-6 * 1e6)
        b, a = self._bilinear_hp(fc_v2a, fs)
        s, self._v2a_hp_z = self._lfilter(b, a, s, self._v2a_hp_z)
        s = self._triode_ecc83(s, gain=0.95, vp_norm=1.3, knee=1.0)
        fc_v2b = 1.0 / (2.0 * np.pi * 0.1e-6 * 1e6)
        b, a = self._bilinear_hp(fc_v2b, fs)
        s, self._v2b_hp_z = self._lfilter(b, a, s, self._v2b_hp_z)
        return s

    def _tonestack(self, samples: np.ndarray) -> np.ndarray:
        fs = self.sample_rate
        IL = 0.13
        fc_bass = 50.0 + self.bass * 250.0
        b, a = self._bilinear_lp(fc_bass, fs)
        s_bass, self._ts_bass_z = self._lfilter(b, a, samples, self._ts_bass_z)
        mid_db = (self.mid - 0.5) * 20.0
        fc_mid = 350.0
        b, a = self._peaking_biquad(fc_mid, Q=0.7, gain_db=mid_db, fs=fs)
        s_mid, self._ts_mid_z = self._lfilter(b, a, s_bass, self._ts_mid_z)
        treble_db = (self.treble - 0.5) * 32.0
        fc_treble = 2200.0
        b, a = self._highshelf_biquad(fc_treble, treble_db, S=1.0, fs=fs)
        s_treble, self._ts_treble_z = self._lfilter(
            b, a, s_mid, self._ts_treble_z)
        out = s_treble * IL * 7.7
        return out

    def _phase_inverter(self, samples: np.ndarray) -> np.ndarray:
        fs = self.sample_rate
        fc_pi = 1.0 / (2.0 * np.pi * 0.022e-6 * 470e3)
        b, a = self._bilinear_hp(fc_pi, fs)
        s, self._pi_hp_z = self._lfilter(b, a, samples, self._pi_hp_z)
        ganho_ltp = 25.0
        assimetria = 0.92
        push = s * ganho_ltp * assimetria
        pull = -s * ganho_ltp
        push_sat = self._triode_ecc83(push, gain=1.0, vp_norm=1.5, knee=0.9)
        pull_sat = self._triode_ecc83(pull, gain=1.0, vp_norm=1.5, knee=0.9)
        combined = (push_sat - pull_sat) * 0.5
        return combined

    def _power_amp(self, samples: np.ndarray) -> np.ndarray:
        fs = self.sample_rate
        s = self._el34_power(samples, bias=0.45, vp_norm=1.0)
        fc_ot_lp = 7000.0
        b_lp, a_lp = self._bilinear_lp(fc_ot_lp, fs)
        s, self._ot_lp_z = self._lfilter(b_lp, a_lp, s, self._ot_lp_z)
        b_bump, a_bump = self._peaking_biquad(
            fc=80.0, Q=1.2, gain_db=3.5, fs=fs
        )
        s, self._ot_bump_z = self._lfilter(b_bump, a_bump, s, self._ot_bump_z)
        presence_db = self.presence * 8.0
        b_pres, a_pres = self._highshelf_biquad(
            fc=2000.0, gain_db=presence_db, S=1.0, fs=fs
        )
        s, self._pres_z = self._lfilter(b_pres, a_pres, s, self._pres_z)
        return s
