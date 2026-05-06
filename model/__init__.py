from model.pedals import boss_distortion_ds1, boss_ns2_noise_suppressor, klon_centaur, boss_ce5_chorus, boss_dd3_delay, boss_rv6_reverb
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
    marshall_plexi_super_lead_1959 = marshall_plexi_super_lead_1959.MarshallPlexiSuperLead1959()
    banco = banco.Banco()

    def salvar_pedais(self):
        for pedal in self.audio.get_pedais():
            if not self.banco.tipo_is_cadastrado(pedal.tipo):
                self.banco.adicionar_pedal(pedal)
            else:
                self.banco.atualizar_pedal(pedal)
        self.banco.conexao.commit()
