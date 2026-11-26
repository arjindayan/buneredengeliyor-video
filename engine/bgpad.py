# yumuşak, davulsuz su altı pedi + hafif marimba notaları (kod üretimi, telifsiz)
# kullanım: python3 engine/bgpad.py <süre_sn> <çıktı.wav>
import numpy as np, sys, wave
sr=44100; dur=float(sys.argv[1]); t=np.arange(int(sr*dur))/sr
chords=[[220,277.18,329.63],[196,246.94,293.66],[174.61,220,261.63],[196,246.94,329.63]]  # A, G, F, G(sus)
out=np.zeros_like(t); L=4.0
for i,c in enumerate(chords*int(dur/L/4+2)):
    s=i*L
    if s>dur: break
    m=(t>=s-1)&(t<s+L+1); tt=t[m]-s
    env=np.clip((tt+1)/1.5,0,1)*np.clip((L+1-tt)/1.5,0,1)
    for fr in c: out[m]+=env*(np.sin(2*np.pi*fr*t[m])+0.3*np.sin(2*np.pi*fr*2.003*t[m]))*0.12
rng=np.random.default_rng(3); notes=[440,523.25,587.33,659.25,783.99]
for k in np.arange(0.5,dur-1,0.75):
    if rng.random()<0.45: continue
    fr=rng.choice(notes); m=(t>=k)&(t<k+1.2); tt=t[m]-k
    out[m]+=np.exp(-tt*5)*np.sin(2*np.pi*fr*t[m])*0.18
out*=1+0.15*np.sin(2*np.pi*0.2*t)
out=np.convolve(out,np.ones(8)/8,'same')
fade=np.clip(np.minimum(t/1.0,(dur-t)/1.5),0,1); out*=fade
out=out/np.abs(out).max()*0.8
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
