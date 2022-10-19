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

            self.last_played_3 = 0
            self.last_played_5 = 0
        except:
            print("Error while loading sound samples, please refer to the readme for more information. Audio disabled.")
            self.audio_enabled = False

    def PlaySound3(self, id: int) -> None:
        if(self.audio_enabled and self.last_played_3 != id):
            if(id & 1 and not self.last_played_3 & 1):
                self.sound_ufo.play(-1)
            elif(not id & 1 and self.last_played_3 & 1):
                self.sound_ufo.stop()
            if(id & 2 and not self.last_played_3 & 2):
                self.sound_shot.play()
            if(id & 4 and not self.last_played_3 & 4):
                self.sound_flash.play()
            if(id & 8 and not self.last_played_3 & 8):
                self.sound_death.play()
            self.last_played_3 = id

    def PlaySound5(self, id: int) -> None:
        if(self.audio_enabled and self.last_played_5 != id):
            if(id & 1 and not self.last_played_5 & 1):
                self.sound_fleet_1.play()
            if(id & 2 and not self.last_played_5 & 2):
                self.sound_fleet_2.play()
            if(id & 4 and not self.last_played_5 & 4):
                self.sound_fleet_3.play()
            if(id & 8 and not self.last_played_5 & 8):
                self.sound_fleet_4.play()
            if(id & 16 and not self.last_played_5 & 16):
                self.sound_ufo_hit.play()
            self.last_played_5 = id
