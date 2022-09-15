from pygame import mixer


class Audio:
    def __init__(self) -> None:
        try:
            self.sound_ufo = mixer.Sound("samples/0.wav")
            self.sound_shot = mixer.Sound("samples/1.wav")
            self.sound_flash = mixer.Sound("samples/2.wav")
            self.sound_death = mixer.Sound("samples/3.wav")
            self.sound_fleet_1 = mixer.Sound("samples/4.wav")
            self.sound_fleet_2 = mixer.Sound("samples/5.wav")
            self.sound_fleet_3 = mixer.Sound("samples/6.wav")
            self.sound_fleet_4 = mixer.Sound("samples/7.wav")
            self.sound_ufo_hit = mixer.Sound("samples/8.wav")
            self.audio_enabled = True
        except:
            print("Error while loading sound samples, please refer to the readme for more information. Audio disabled.")
            self.audio_enabled = False

    def PlaySoundUFOLoop(self) -> None:
        if(self.audio_enabled): self.sound_ufo.play(-1)

    def StopSoundUFOLoop(self) -> None:
        if(self.audio_enabled): self.sound_ufo.stop()

    def PlaySoundShot(self) -> None:
        if(self.audio_enabled): self.sound_shot.play()

    def PlaySoundFlash(self) -> None:
        if(self.audio_enabled): self.sound_flash.play()

    def PlaySoundDeath(self) -> None:
        if(self.audio_enabled): self.sound_death.play()

    def PlaySoundFleet1(self) -> None:
        if(self.audio_enabled): self.sound_fleet_1.play()

    def PlaySoundFleet2(self) -> None:
        if(self.audio_enabled): self.sound_fleet_2.play()

    def PlaySoundFleet3(self) -> None:
        if(self.audio_enabled): self.sound_fleet_3.play()

    def PlaySoundFleet4(self) -> None:
        if(self.audio_enabled): self.sound_fleet_4.play()

    def PlaySoundUFOHit(self) -> None:
        if(self.audio_enabled): self.sound_ufo_hit.play()

