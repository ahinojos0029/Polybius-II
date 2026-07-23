# audio.py
import array
import random
import pygame

def gen_square_wave(freq, duration, volume, master_volume):
    vol = volume * master_volume
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array("h")
    period = sample_rate / max(1, freq)
    for i in range(n_samples):
        val = 32000 if (i % period) < (period / 2) else -32000
        buf.append(int(val * vol * (1.0 - (i / float(n_samples)))))
    return pygame.mixer.Sound(buf)

def gen_laser_chirp(start_freq, end_freq, duration, volume, master_volume):
    vol = volume * master_volume
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array("h")
    phase = 0.0
    for i in range(n_samples):
        t = i / float(n_samples)
        curr_freq = start_freq + (end_freq - start_freq) * t
        phase += curr_freq / sample_rate
        val = 32000 if (phase % 1.0) < 0.5 else -32000
        buf.append(int(val * vol * (1.0 - t)))
    return pygame.mixer.Sound(buf)

def gen_8bit_noise_explosion(duration, volume, master_volume):
    vol = volume * master_volume
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array("h")
    for i in range(n_samples):
        decay = (1.0 - (i / float(n_samples))) ** 2
        buf.append(int(random.choice([28000, -28000]) * vol * decay))
    return pygame.mixer.Sound(buf)

def gen_stage_clear_jingle(volume, master_volume):
    vol = volume * master_volume
    sample_rate = 22050
    duration = 0.6
    n_samples = int(sample_rate * duration)
    buf = array.array("h")
    notes = [440, 554, 659, 880]
    chunk = n_samples // len(notes)
    for i in range(n_samples):
        freq = notes[min(len(notes) - 1, i // chunk)]
        period = sample_rate / max(1, freq)
        val = 32000 if (i % period) < (period / 2) else -32000
        decay = 1.0 - (i / float(n_samples))
        buf.append(int(val * vol * decay))
    return pygame.mixer.Sound(buf)

def gen_powerup_sound(volume, master_volume):
    vol = volume * master_volume
    sample_rate = 22050
    duration = 0.25
    n_samples = int(sample_rate * duration)
    buf = array.array("h")
    for i in range(n_samples):
        freq = 300 + (i * 3.0)
        period = sample_rate / max(1, freq)
        val = 32000 if (i % period) < (period / 2) else -32000
        decay = 1.0 - (i / float(n_samples))
        buf.append(int(val * vol * decay))
    return pygame.mixer.Sound(buf)

class SoundManager:
    def __init__(self, master_volume):
        self.rebuild_sounds(master_volume)
        self.chan_sfx = pygame.mixer.Channel(0)
        self.chan_explode = pygame.mixer.Channel(1)
        self.chan_hum = pygame.mixer.Channel(2)
        self.chan_music = pygame.mixer.Channel(3)

    def rebuild_sounds(self, master_volume):
        self.snd_laser = gen_laser_chirp(850, 180, 0.07, 0.2, master_volume)
        self.snd_explode = gen_8bit_noise_explosion(0.35, 0.35, master_volume)
        self.snd_hit = gen_laser_chirp(1200, 600, 0.04, 0.2, master_volume)
        self.snd_stage_clear = gen_stage_clear_jingle(0.3, master_volume)
        self.snd_powerup = gen_powerup_sound(0.25, master_volume)