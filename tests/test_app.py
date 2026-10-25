import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
import pytest
from aimtrainer.app import Game
from aimtrainer.model import Target


@pytest.fixture
def game(tmp_path):
    g=Game(tmp_path,silent=True)
    yield g
    pygame.quit()


def key(g,value):
    g.handle(pygame.event.Event(pygame.KEYDOWN,key=value,mod=0))


def begin(g,mode='classic'):
    g.mode=mode;g.start();g.update(3.1);g.render();assert g.screen=='playing'


def test_pause_freezes_all_gameplay(game):
    begin(game);game.update(.2);game.session.combo=7;game.session.last_hit=game.session.elapsed
    game.effects=[[300,300,50,10,.4]];key(game,pygame.K_ESCAPE)
    before=(game.session.elapsed,game.session.combo,game.session.targets[0].age,list(game.effects[0]))
    game.update(99)
    assert before==(game.session.elapsed,game.session.combo,game.session.targets[0].age,list(game.effects[0]))
    key(game,pygame.K_ESCAPE);assert game.screen=='playing'
    game.update(.1);assert game.session.elapsed>before[0]


def test_focus_loss_pauses_tracking(game):
    begin(game,'tracking');game.holding=True;game.handle(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert game.screen=='paused' and not game.holding


def test_countdown_focus_loss(game):
    game.start();game.handle(pygame.event.Event(pygame.WINDOWFOCUSLOST));assert game.screen=='ready'
    key(game,pygame.K_RETURN);assert game.screen=='countdown' and game.countdown==3


def test_resized_click_uses_event_position(game):
    game.handle(pygame.event.Event(pygame.VIDEORESIZE,w=1000,h=800));begin(game)
    game.session.targets=[Target(400,400,40,3,0,age=.3)]
    x,y,w,h=game.viewport;pos=(round(x+400*w/1440),round(y+400*h/900));game.pointer=(100,100)
    game.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=pos,button=1));assert game.session.hits==1


def test_back_never_starts_game(game):
    game.show('settings');key(game,pygame.K_ESCAPE);assert game.screen=='training' and game.session is None


def test_results_save_once_and_restart(game):
    begin(game);game.session.finish();game.update(.01)
    assert game.screen=='results' and len(game.store.sessions)==1
    game.finish();assert len(game.store.sessions)==1
    game.render();assert any(b.action=='restart' for b in game.ui.buttons)
    key(game,pygame.K_r);assert game.screen=='countdown' and game.session.elapsed==0
    game.handle(pygame.event.Event(pygame.QUIT));assert not game.running


def test_keyboard_and_profile_input(game):
    key(game,pygame.K_TAB);assert game.focus==0
    game.show('profiles');game.action('edit_profile');game.handle(pygame.event.Event(pygame.TEXTINPUT,text='Meazbah'))
    key(game,pygame.K_RETURN);assert game.store.active=='Meazbah'


@pytest.mark.parametrize('screen',['training','settings','profiles','statistics','help'])
def test_screen_buttons_in_bounds(game,screen):
    game.show(screen);game.render();assert game.ui.buttons
    assert all(pygame.Rect(0,0,1440,900).contains(b.rect) for b in game.ui.buttons)


def test_practice_end_saves(game):
    begin(game,'practice');game.action('pause');game.action('end')
    assert game.screen=='results' and game.store.sessions[-1]['reason']=='Practice ended'


def test_audio_failure_is_optional(tmp_path,monkeypatch):
    def fail(*a,**k):raise pygame.error('no audio device')
    monkeypatch.setattr(pygame.mixer,'init',fail);g=Game(tmp_path)
    assert not g.audio.available and g.running;pygame.quit()


def test_reduced_motion(game):
    begin(game);game.settings.reduced_motion=True;game.session.events=[('hit',(400,400)),('miss',(500,500))]
    game.update(.01);assert game.effects==[] and game.flash==0


def test_letterbox_coordinate_mapping_ignores_black_bars(game):
    game.handle(pygame.event.Event(pygame.VIDEORESIZE,w=1000,h=800))
    x,y,w,h=game.viewport
    assert game.map_point((x+w/2,y+h/2))==pytest.approx((720,450))
    assert game.map_point((500,10)) is None


def test_fullscreen_toggle_returns_to_windowed_size(game):
    before=game.window.get_size()
    game.toggle_fullscreen();assert game.fullscreen
    game.toggle_fullscreen();assert not game.fullscreen and game.window.get_size()==before
