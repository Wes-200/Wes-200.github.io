"""Generate an original, upbeat, royalty-free backing track (no copyright).
Bright C-major pop/electronic loop: pad + plucked arpeggio + bass + soft beat.
Output: ../assets/demo-music.wav
"""
import numpy as np, wave, struct, os

SR = 44100
BPM = 118
beat = 60.0 / BPM
bar = beat * 4
BARS = 20                      # ~40s
DUR = bar * BARS
N = int(DUR * SR)
t = np.arange(N) / SR

def note(n):  # midi -> freq
    return 440.0 * 2 ** ((n - 69) / 12.0)

# C major friendly progression: C  G  Am  F  (I V vi IV)
prog = [
    [60, 64, 67],   # C
    [55, 59, 62],   # G
    [57, 60, 64],   # Am
    [53, 57, 60],   # F
]
roots = [48, 43, 45, 41]

def adsr(length, a, d, s, r, sl=0.7):
    e = np.zeros(length)
    a_n=int(a*SR); d_n=int(d*SR); r_n=int(r*SR)
    s_n=max(0, length-a_n-d_n-r_n)
    i=0
    if a_n: e[i:i+a_n]=np.linspace(0,1,a_n); i+=a_n
    if d_n: e[i:i+d_n]=np.linspace(1,sl,d_n); i+=d_n
    if s_n: e[i:i+s_n]=sl; i+=s_n
    if r_n: e[i:i+r_n]=np.linspace(sl,0,r_n); i+=r_n
    return e[:length]

pad = np.zeros(N); arp = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N)

for b in range(BARS):
    chord = prog[b % 4]; root = roots[b % 4]
    s0 = int(b*bar*SR); s1 = int((b+1)*bar*SR); L = s1-s0
    tt = np.arange(L)/SR
    # pad (soft chord)
    env = adsr(L, 0.08, 0.2, 0.6, 0.5, 0.6)
    for m in chord:
        f = note(m+12)
        pad[s0:s1] += (np.sin(2*np.pi*f*tt) + 0.4*np.sin(2*np.pi*2*f*tt)) * env
    # bass (root, per beat)
    for k in range(4):
        bs=int((b*bar+k*beat)*SR); be=int((b*bar+(k+1)*beat)*SR); bl=be-bs
        bt=np.arange(bl)/SR
        be_env=adsr(bl,0.005,0.05,0.8,0.06,0.8)
        bass[bs:be] += np.sin(2*np.pi*note(root)*bt)*be_env
    # arpeggio (eighth notes up the chord, plucky)
    arp_notes = [chord[0], chord[1], chord[2], chord[1]] * 2  # 8 per bar
    for k in range(8):
        ns=int((b*bar+k*(beat/2))*SR); ne=int((b*bar+(k+1)*(beat/2))*SR); nl=ne-ns
        nt=np.arange(nl)/SR
        f=note(arp_notes[k]+12)
        penv=np.exp(-nt*9)
        arp[ns:ne] += (np.sin(2*np.pi*f*nt)+0.25*np.sin(2*np.pi*3*f*nt))*penv
    # drums: kick on beats, hat on offbeats
    for k in range(4):
        ks=int((b*bar+k*beat)*SR); kl=int(0.13*SR)
        if ks+kl<=N:
            kt=np.arange(kl)/SR
            fsweep=110*np.exp(-kt*32)+50
            drums[ks:ks+kl]+= np.sin(2*np.pi*fsweep*kt)*np.exp(-kt*22)*1.0
        hs=int((b*bar+k*beat+beat/2)*SR); hl=int(0.04*SR)
        if hs+hl<=N:
            ht=np.arange(hl)/SR
            drums[hs:hs+hl]+= (np.random.rand(hl)*2-1)*np.exp(-ht*60)*0.25

mix = 0.16*pad + 0.22*arp + 0.20*bass + 0.5*drums
# gentle soft-clip
mix = np.tanh(mix*1.1)
mix /= np.max(np.abs(mix))+1e-9
mix *= 0.85
# fade in / out
fi=int(0.4*SR); fo=int(2.2*SR)
mix[:fi]*=np.linspace(0,1,fi); mix[-fo:]*=np.linspace(1,0,fo)

out = os.path.join(os.path.dirname(__file__), '..', 'assets', 'demo-music.wav')
data=(mix*32767).astype(np.int16)
with wave.open(out,'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(data.tobytes())
print('wrote', out, round(DUR,1),'s')
