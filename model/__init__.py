from model.pedals import boss_distortion_ds1, boss_ns2_noise_suppressor, klon_centaur, boss_ce5_chorus, boss_dd3_delay, boss_rv6_reverb, dunlop_cry_baby_gcb95
from model import audio
from model.amps import marshall_plexi_super_lead_1959
from database import banco


class Init:
    audio = audio.Audio()
    boss_distortion_ds12 = boss_distortion_ds1.BossDistortionDS1()
    boss_ns2_noise_suppressor = boss_ns2_noise_suppressor.NS2NoiseSuppressor()
    klon_centaur = klon_centaur.KlonCentaur()
    boss_ce5_chorus = boss_ce5_chorus.BossCE5Chorus()
    boss_dd3_delay = boss_dd3_delay.BossDD3Delay()
    boss_rv6_reverb = boss_rv6_reverb.BossRV6Reverb()
    dunlop_cry_baby_gcb95 = dunlop_cry_baby_gcb95.DunlopCryBabyGCB95()
    marshall_plexi_super_lead_1959 = marshall_plexi_super_lead_1959.MarshallPlexiSuperLead1959()
    banco = banco.Banco()

    
    audio.add_pedal(boss_distortion_ds12)
    audio.add_pedal(boss_ns2_noise_suppressor)
    audio.add_pedal(klon_centaur)
    audio.add_pedal(boss_ce5_chorus)
    audio.add_pedal(boss_dd3_delay)
    audio.add_pedal(boss_rv6_reverb)
    audio.add_pedal(dunlop_cry_baby_gcb95)
    audio.add_amp(marshall_plexi_super_lead_1959)

