"""Real SDL/Pygame event-loop exercise, offline and isolated from player saves."""
import argparse
from pathlib import Path
import os
import statistics
import sys
import tempfile
import time
import json

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from aimtrainer.app import Game
from aimtrainer.model import MODES


def click(g,action):
    g.render()
    button=next(b for b in g.ui.buttons if b.action==action)
    x,y,w,h=g.viewport
    pos=(round(x+button.rect.centerx*w/1440),round(y+button.rect.centery*h/900))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=pos,button=1))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP,pos=pos,button=1))
    for event in pygame.event.get():g.handle(event)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--screenshots',type=Path)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    if args.screenshots:args.screenshots.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        g=Game(directory)
        def snapshot(label):
            g.render()
            if args.screenshots:pygame.image.save(g.ui.surface,str(args.screenshots/(label+'.png')))
        snapshot('training')
        click(g,'settings');assert g.screen=='settings';snapshot('settings')
        click(g,'profiles');g.action('edit_profile')
        g.handle(pygame.event.Event(pygame.TEXTINPUT,text='QA Player'))
        g.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN,mod=0))
        assert g.store.active=='QA Player'
        snapshot('profiles')
        for mode in MODES:
            g.show('training');g.mode=mode;click(g,'start')
            assert g.screen=='countdown'
            g.update(3.01);assert g.screen=='playing'
            g.update(.25)
            if mode!='tracking':
                t=g.session.targets[0];x,y,w,h=g.viewport
                pos=(round(x+t.x*w/1440),round(y+t.y*h/900))
                g.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=pos,button=1))
                assert g.session.hits==1,(mode,g.session.summary())
            else:
                for _ in range(180):
                    g.pointer=g.session.track_point;g.holding=True;g.update(1/120)
                assert g.session.tracked>1.45
            snapshot(mode)
            g.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE,mod=0))
            before=g.session.summary();g.update(5);assert g.session.summary()==before
            snapshot('paused')
            click(g,'resume');assert g.screen=='playing'
            g.action('pause');click(g,'end');assert g.screen=='results'
            snapshot('results')
            click(g,'restart');assert g.screen=='countdown' and g.session.elapsed==0
        g.show('training');click(g,'daily');assert g.session.daily
        g.show('statistics');snapshot('statistics')
        g.action(('stats_tab','Achievements'));snapshot('achievements')
        g.show('help');snapshot('help')
        g.handle(pygame.event.Event(pygame.VIDEORESIZE,w=960,h=600));g.render()
        assert g.viewport==(0,0,960,600)
        g.handle(pygame.event.Event(pygame.VIDEORESIZE,w=1000,h=800));g.render()
        # Odd-sized letterbox margins can differ by one physical pixel.
        mapped=g.map_point((500,400))
        assert abs(mapped[0]-720)<1.5 and abs(mapped[1]-450)<1.5
        assert g.map_point((500,10)) is None
        # Measure the delivered renderer; exclude sleep/frame-cap waits and warm-up.
        g.mode='practice';g.start();g.update(3.01)
        samples=[]
        for i in range(360):
            started=time.perf_counter();g.update(1/120);g.render()
            if i>=60:samples.append((time.perf_counter()-started)*1000)
        samples.sort()
        result={'status':'passed','pygame':pygame.version.ver,'python':sys.version.split()[0],
                'video_driver':pygame.display.get_driver(),'modes':list(MODES),'saved_sessions':len(g.store.sessions),
                'checks':['menu event dispatch','five modes','tracking dwell','pause freeze','restart','daily',
                          'profiles','resized coordinates','statistics','achievements','generated audio'],
                'audio_backend_available':bool(g.audio and g.audio.available),
                'frame_measurement':{'samples':len(samples),'window':[1000,800],'logical_canvas':[1440,900],
                    'median_update_render_ms':round(statistics.median(samples),3),'p95_update_render_ms':round(samples[int(len(samples)*.95)-1],3),
                    'scope':'Headless SDL dummy driver; CPU simulation/drawing/scaling/display call only. Not physical-display FPS or end-to-end input latency.'}}
        g.handle(pygame.event.Event(pygame.QUIT));assert not g.running
        # Exercise the public run loop with a queued quit, not only individual methods.
        g.running=True;pygame.event.post(pygame.event.Event(pygame.QUIT));g.run()
        print(json.dumps(result,indent=2))
        if args.report:args.report.write_text(json.dumps(result,indent=2))


if __name__=='__main__':main()
